DROP SCHEMA IF EXISTS task_governance CASCADE;
CREATE SCHEMA task_governance;

SET search_path TO task_governance;

CREATE TYPE task_state AS ENUM (
    'todo',
    'in_progress',
    'done'
);

CREATE TYPE task_priority AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE pr_state AS ENUM (
    'draft',
    'open',
    'closed',
    'merged'
);

CREATE TYPE review_state AS ENUM (
    'commented',
    'approved',
    'changes_requested',
    'dismissed'
);

CREATE TYPE check_state AS ENUM (
    'pending',
    'passing',
    'failing'
);

CREATE TYPE merge_strategy AS ENUM (
    'merge_commit',
    'squash',
    'rebase'
);

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    owner TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(name)) >= 2),
    CHECK (length(trim(owner)) >= 2)
);

CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (username ~ '^[a-zA-Z0-9._-]{2,64}$')
);

CREATE TABLE branches (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    name TEXT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    UNIQUE (repository_id, name),
    CHECK (length(trim(name)) >= 1)
);

CREATE TABLE commits (
    commit_id BIGSERIAL PRIMARY KEY,
    branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    sha CHAR(12) NOT NULL UNIQUE,
    author_id BIGINT NOT NULL
        REFERENCES users(user_id),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(message)) > 0)
);

CREATE TABLE pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    source_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    author_id BIGINT NOT NULL
        REFERENCES users(user_id),
    state pr_state NOT NULL DEFAULT 'draft',
    head_commit_id BIGINT REFERENCES commits(commit_id),
    merge_strategy merge_strategy,
    merged_by BIGINT REFERENCES users(user_id),
    merged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ,
    UNIQUE (repository_id, number),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (length(trim(title)) > 0)
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    commit_id BIGINT NOT NULL
        REFERENCES commits(commit_id)
        ON DELETE CASCADE,
    sequence_no INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, sequence_no),
    CHECK (sequence_no > 0)
);

CREATE TABLE review_requests (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL
        REFERENCES users(user_id),
    requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (pull_request_id, reviewer_id)
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL
        REFERENCES users(user_id),
    state review_state NOT NULL,
    reviewed_commit_id BIGINT NOT NULL
        REFERENCES commits(commit_id),
    body TEXT NOT NULL DEFAULT '',
    dismissed BOOLEAN NOT NULL DEFAULT FALSE,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (pull_request_id, review_id),
    CHECK (length(body) <= 10000)
);

CREATE TABLE review_comments (
    comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES reviews(review_id)
        ON DELETE CASCADE,
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(body)) > 0)
);

CREATE TABLE conversations (
    conversation_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    author_id BIGINT NOT NULL
        REFERENCES users(user_id),
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    CHECK (length(trim(body)) > 0)
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state check_state NOT NULL,
    commit_id BIGINT NOT NULL
        REFERENCES commits(commit_id),
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE
        REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    required_reviews INTEGER NOT NULL DEFAULT 0,
    restrict_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_force_push BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_deletion BOOLEAN NOT NULL DEFAULT TRUE,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    allow_administrator_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (required_reviews >= 0)
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (policy_id, check_name)
);

CREATE TABLE tasks (
    task_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    state task_state NOT NULL DEFAULT 'todo',
    priority task_priority NOT NULL DEFAULT 'medium',
    linked_pull_request_id BIGINT
        REFERENCES pull_requests(pull_request_id),
    created_by BIGINT NOT NULL
        REFERENCES users(user_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(title)) > 0)
);

CREATE INDEX idx_branches_repository
    ON branches(repository_id);

CREATE INDEX idx_commits_branch_created
    ON commits(branch_id, created_at DESC);

CREATE INDEX idx_pull_requests_target_state
    ON pull_requests(target_branch_id, state);

CREATE INDEX idx_reviews_pr_commit_state
    ON reviews(pull_request_id, reviewed_commit_id, state);

CREATE INDEX idx_status_checks_pr_state
    ON status_checks(pull_request_id, state);

CREATE INDEX idx_tasks_repository_state_priority
    ON tasks(repository_id, state, priority);

CREATE OR REPLACE FUNCTION set_task_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_tasks_updated_at
BEFORE UPDATE ON tasks
FOR EACH ROW
EXECUTE FUNCTION set_task_updated_at();

CREATE OR REPLACE FUNCTION enforce_pull_request_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    source_repository BIGINT;
    target_repository BIGINT;
BEGIN
    SELECT repository_id
    INTO source_repository
    FROM branches
    WHERE branch_id = NEW.source_branch_id;

    SELECT repository_id
    INTO target_repository
    FROM branches
    WHERE branch_id = NEW.target_branch_id;

    IF source_repository IS NULL
       OR target_repository IS NULL
       OR source_repository <> target_repository
       OR source_repository <> NEW.repository_id THEN
        RAISE EXCEPTION
            'Pull request branches must belong to the same repository';
    END IF;

    IF NEW.source_branch_id = NEW.target_branch_id THEN
        RAISE EXCEPTION
            'Pull request source and target cannot be identical';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_pull_request_integrity
BEFORE INSERT OR UPDATE ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION enforce_pull_request_integrity();

CREATE OR REPLACE FUNCTION prevent_invalid_merge()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.state = 'merged'
       AND OLD.state <> 'merged'
       AND (
            NEW.merge_strategy IS NULL
            OR NEW.merged_by IS NULL
            OR NEW.merged_at IS NULL
       ) THEN
        RAISE EXCEPTION
            'Merged pull requests require strategy, merger and timestamp';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_merge_integrity
BEFORE UPDATE ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION prevent_invalid_merge();

CREATE OR REPLACE FUNCTION merge_eligibility(
    p_pull_request_id BIGINT,
    p_actor_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    pr RECORD;
    policy RECORD;
    approval_count INTEGER;
    unresolved_count INTEGER;
    missing_checks INTEGER;
BEGIN
    SELECT
        pr.*,
        target.branch_id AS target_branch_id
    INTO pr
    FROM pull_requests pr
    JOIN branches target
      ON target.branch_id = pr.target_branch_id
    WHERE pr.pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 'Pull request does not exist';
        RETURN;
    END IF;

    IF pr.state <> 'open' THEN
        RETURN QUERY
        SELECT FALSE, 'Pull request is not open';
    END IF;

    IF pr.author_id = p_actor_id THEN
        RETURN QUERY
        SELECT FALSE, 'Author cannot merge its own pull request';
    END IF;

    SELECT bp.*
    INTO policy
    FROM branch_protection_policies bp
    WHERE bp.branch_id = pr.target_branch_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT TRUE, 'No branch protection policy is configured';
        RETURN;
    END IF;

    SELECT COUNT(DISTINCT reviewer_id)
    INTO approval_count
    FROM reviews
    WHERE pull_request_id = p_pull_request_id
      AND state = 'approved'
      AND dismissed = FALSE
      AND reviewed_commit_id = pr.head_commit_id;

    IF approval_count < policy.required_reviews THEN
        RETURN QUERY
        SELECT
            FALSE,
            format(
                'Required approvals: %s, current approvals: %s',
                policy.required_reviews,
                approval_count
            );
    END IF;

    SELECT COUNT(*)
    INTO missing_checks
    FROM required_status_checks required
    WHERE required.policy_id = policy.policy_id
      AND NOT EXISTS (
          SELECT 1
          FROM status_checks actual
          WHERE actual.pull_request_id = p_pull_request_id
            AND actual.check_name = required.check_name
            AND actual.state = 'passing'
            AND actual.commit_id = pr.head_commit_id
      );

    IF missing_checks > 0 THEN
        RETURN QUERY
        SELECT
            FALSE,
            format(
                '%s required status check(s) are missing or stale',
                missing_checks
            );
    END IF;

    IF policy.require_conversation_resolution THEN
        SELECT COUNT(*)
        INTO unresolved_count
        FROM conversations
        WHERE pull_request_id = p_pull_request_id
          AND resolved = FALSE;

        IF unresolved_count > 0 THEN
            RETURN QUERY
            SELECT
                FALSE,
                format(
                    '%s unresolved conversation(s)',
                    unresolved_count
                );
        END IF;

        SELECT COUNT(*)
        INTO unresolved_count
        FROM review_comments rc
        JOIN reviews r
          ON r.review_id = rc.review_id
        WHERE r.pull_request_id = p_pull_request_id
          AND rc.resolved = FALSE;

        IF unresolved_count > 0 THEN
            RETURN QUERY
            SELECT
                FALSE,
                format(
                    '%s unresolved review comment(s)',
                    unresolved_count
                );
        END IF;
    END IF;

    RETURN QUERY
    SELECT TRUE, 'All merge conditions satisfied';
END;
$$;

CREATE OR REPLACE VIEW v_task_governance_dashboard AS
SELECT
    t.task_id,
    t.title,
    t.state AS task_state,
    t.priority,
    r.name AS repository,
    pr.number AS pull_request_number,
    pr.state AS pull_request_state,
    source.name AS source_branch,
    target.name AS target_branch,
    pr.head_commit_id,
    COALESCE(
        (
            SELECT bool_and(me.eligible)
            FROM merge_eligibility(
                pr.pull_request_id,
                pr.author_id
            ) me
        ),
        FALSE
    ) AS merge_eligible
FROM tasks t
JOIN repositories r
  ON r.repository_id = t.repository_id
LEFT JOIN pull_requests pr
  ON pr.pull_request_id = t.linked_pull_request_id
LEFT JOIN branches source
  ON source.branch_id = pr.source_branch_id
LEFT JOIN branches target
  ON target.branch_id = pr.target_branch_id;

INSERT INTO repositories(name, owner)
VALUES ('interactive-task-manager', 'acme');

INSERT INTO users(username, display_name)
VALUES
    ('platform-admin', 'Platform Administrator'),
    ('developer', 'Primary Developer'),
    ('reviewer-one', 'Reviewer One'),
    ('reviewer-two', 'Reviewer Two'),
    ('release-manager', 'Release Manager');

INSERT INTO branches(repository_id, name)
SELECT repository_id, 'main'
FROM repositories
WHERE name = 'interactive-task-manager';

INSERT INTO commits(
    branch_id,
    sha,
    author_id,
    message
)
SELECT
    b.branch_id,
    'main00000001',
    u.user_id,
    'Initialize task management platform'
FROM branches b
JOIN repositories r
  ON r.repository_id = b.repository_id
JOIN users u
  ON u.username = 'platform-admin'
WHERE r.name = 'interactive-task-manager'
  AND b.name = 'main';

UPDATE branches
SET protected = TRUE
WHERE name = 'main';

INSERT INTO branch_protection_policies(
    branch_id,
    required_reviews,
    restrict_direct_push,
    restrict_force_push,
    restrict_deletion,
    require_conversation_resolution,
    require_linear_history
)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE
FROM branches
WHERE name = 'main';

INSERT INTO required_status_checks(policy_id, check_name)
SELECT
    policy_id,
    check_name
FROM branch_protection_policies
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan')
) AS checks(check_name);

INSERT INTO branches(repository_id, name)
SELECT repository_id, 'feature/task-board'
FROM repositories
WHERE name = 'interactive-task-manager';

INSERT INTO commits(
    branch_id,
    sha,
    author_id,
    message
)
SELECT
    b.branch_id,
    'feat00000001',
    u.user_id,
    'Add interactive task state transitions'
FROM branches b
JOIN repositories r
  ON r.repository_id = b.repository_id
JOIN users u
  ON u.username = 'developer'
WHERE r.name = 'interactive-task-manager'
  AND b.name = 'feature/task-board';

INSERT INTO commits(
    branch_id,
    sha,
    author_id,
    message
)
SELECT
    b.branch_id,
    'feat00000002',
    u.user_id,
    'Add pull request governance controls'
FROM branches b
JOIN repositories r
  ON r.repository_id = b.repository_id
JOIN users u
  ON u.username = 'developer'
WHERE r.name = 'interactive-task-manager'
  AND b.name = 'feature/task-board';

INSERT INTO pull_requests(
    repository_id,
    number,
    title,
    source_branch_id,
    target_branch_id,
    author_id,
    state,
    head_commit_id
)
SELECT
    r.repository_id,
    1,
    'Build governed task workflow',
    source.branch_id,
    target.branch_id,
    author.user_id,
    'open',
    head.commit_id
FROM repositories r
JOIN branches source
  ON source.repository_id = r.repository_id
 AND source.name = 'feature/task-board'
JOIN branches target
  ON target.repository_id = r.repository_id
 AND target.name = 'main'
JOIN users author
  ON author.username = 'developer'
JOIN commits head
  ON head.branch_id = source.branch_id
 AND head.sha = 'feat00000002'
WHERE r.name = 'interactive-task-manager';

INSERT INTO pull_request_commits(
    pull_request_id,
    commit_id,
    sequence_no
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    ROW_NUMBER() OVER (ORDER BY c.created_at)
FROM pull_requests pr
JOIN branches source
  ON source.branch_id = pr.source_branch_id
JOIN commits c
  ON c.branch_id = source.branch_id
WHERE pr.number = 1;

INSERT INTO review_requests(
    pull_request_id,
    reviewer_id
)
SELECT
    pr.pull_request_id,
    u.user_id
FROM pull_requests pr
CROSS JOIN users u
WHERE pr.number = 1
  AND u.username IN ('reviewer-one', 'reviewer-two');

INSERT INTO reviews(
    pull_request_id,
    reviewer_id,
    state,
    reviewed_commit_id,
    body
)
SELECT
    pr.pull_request_id,
    reviewer.user_id,
    'changes_requested',
    pr.head_commit_id,
    'Validate task state transitions before persistence.'
FROM pull_requests pr
JOIN users reviewer
  ON reviewer.username = 'reviewer-one'
WHERE pr.number = 1;

INSERT INTO review_comments(
    review_id,
    body
)
SELECT
    review_id,
    'Reject invalid task state transitions.'
FROM reviews
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE number = 1
);

INSERT INTO conversations(
    pull_request_id,
    author_id,
    body
)
SELECT
    pr.pull_request_id,
    u.user_id,
    'State transitions require explicit validation.'
FROM pull_requests pr
JOIN users u
  ON u.username = 'reviewer-one'
WHERE pr.number = 1;

INSERT INTO reviews(
    pull_request_id,
    reviewer_id,
    state,
    reviewed_commit_id,
    body
)
SELECT
    pr.pull_request_id,
    reviewer.user_id,
    'approved',
    pr.head_commit_id,
    'Implementation reviewed after validation discussion.'
FROM pull_requests pr
JOIN users reviewer
  ON reviewer.username = 'reviewer-one'
WHERE pr.number = 1;

INSERT INTO reviews(
    pull_request_id,
    reviewer_id,
    state,
    reviewed_commit_id,
    body
)
SELECT
    pr.pull_request_id,
    reviewer.user_id,
    'approved',
    pr.head_commit_id,
    'Reviewed task workflow and governance controls.'
FROM pull_requests pr
JOIN users reviewer
  ON reviewer.username = 'reviewer-two'
WHERE pr.number = 1;

INSERT INTO status_checks(
    pull_request_id,
    check_name,
    state,
    commit_id,
    completed_at
)
SELECT
    pr.pull_request_id,
    checks.check_name,
    'passing',
    pr.head_commit_id,
    now()
FROM pull_requests pr
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan')
) AS checks(check_name)
WHERE pr.number = 1;

UPDATE review_comments
SET resolved = TRUE
WHERE review_id IN (
    SELECT review_id
    FROM reviews
    WHERE pull_request_id = (
        SELECT pull_request_id
        FROM pull_requests
        WHERE number = 1
    )
)
AND resolved = FALSE;

UPDATE conversations
SET resolved = TRUE,
    resolved_at = now()
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE number = 1
);

INSERT INTO tasks(
    repository_id,
    title,
    description,
    state,
    priority,
    linked_pull_request_id,
    created_by
)
SELECT
    r.repository_id,
    'Build governed task workflow',
    'Track engineering work through review-controlled changes.',
    'in_progress',
    'high',
    pr.pull_request_id,
    u.user_id
FROM repositories r
JOIN pull_requests pr
  ON pr.repository_id = r.repository_id
 AND pr.number = 1
JOIN users u
  ON u.username = 'developer'
WHERE r.name = 'interactive-task-manager';

-- The following query exposes every condition that affects merge eligibility.
SELECT
    eligible,
    reason
FROM merge_eligibility(
    (
        SELECT pull_request_id
        FROM pull_requests
        WHERE number = 1
    ),
    (
        SELECT user_id
        FROM users
        WHERE username = 'release-manager'
    )
);

-- Aggregated task report by priority and workflow state.
SELECT
    priority,
    state,
    COUNT(*) AS task_count
FROM tasks
GROUP BY priority, state
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        ELSE 4
    END,
    state;

-- Required checks and their current state.
SELECT
    pr.number,
    sc.check_name,
    sc.state,
    sc.commit_id = pr.head_commit_id AS is_current
FROM pull_requests pr
JOIN status_checks sc
  ON sc.pull_request_id = pr.pull_request_id
ORDER BY pr.number, sc.check_name;

-- Reviewer decision report.
SELECT
    pr.number,
    u.username AS reviewer,
    r.state,
    r.dismissed,
    r.reviewed_commit_id = pr.head_commit_id AS is_current
FROM reviews r
JOIN pull_requests pr
  ON pr.pull_request_id = r.pull_request_id
JOIN users u
  ON u.user_id = r.reviewer_id
ORDER BY pr.number, u.username;

-- A transactional merge state transition. The transaction is rolled back
-- deliberately so the sample database remains useful for repeated execution.
BEGIN;

SELECT pg_advisory_xact_lock(
    (
        SELECT pull_request_id
        FROM pull_requests
        WHERE number = 1
    )
);

DO $$
DECLARE
    v_pr_id BIGINT;
    v_actor BIGINT;
    v_eligible BOOLEAN;
BEGIN
    SELECT pull_request_id
    INTO v_pr_id
    FROM pull_requests
    WHERE number = 1
    FOR UPDATE;

    SELECT user_id
    INTO v_actor
    FROM users
    WHERE username = 'release-manager';

    SELECT bool_and(me.eligible)
    INTO v_eligible
    FROM merge_eligibility(v_pr_id, v_actor) me;

    IF NOT COALESCE(v_eligible, FALSE) THEN
        RAISE EXCEPTION 'Pull request is not merge eligible';
    END IF;

    UPDATE pull_requests
    SET state = 'merged',
        merge_strategy = 'squash',
        merged_by = v_actor,
        merged_at = now(),
        closed_at = now()
    WHERE pull_request_id = v_pr_id;

    UPDATE tasks
    SET state = 'done'
    WHERE linked_pull_request_id = v_pr_id;
END;
$$;

ROLLBACK;

-- Final read-only governance dashboard.
SELECT *
FROM v_task_governance_dashboard
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        ELSE 4
    END,
    task_id;
