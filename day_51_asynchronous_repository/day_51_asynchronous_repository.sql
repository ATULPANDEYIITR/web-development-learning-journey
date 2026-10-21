-- PostgreSQL repository-governance model.
--
-- The relational model separates:
-- Pull Requests: proposed changes and their lifecycle
-- Code Reviews: evaluations tied to a specific PR head
-- Approvals: APPROVED review states and their freshness
-- Branch Protection: repository-level rules controlling merge eligibility
--
-- The asynchronous JavaScript theme is represented by workflow status:
-- status checks can be queued/running/completed independently before the
-- database transaction evaluates whether a Pull Request is mergeable.

DROP VIEW IF EXISTS merge_eligibility_report;
DROP FUNCTION IF EXISTS evaluate_pull_request(integer);
DROP FUNCTION IF EXISTS invalidate_stale_approvals();
DROP FUNCTION IF EXISTS set_review_timestamp();
DROP TABLE IF EXISTS review_comments CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS status_checks CASCADE;
DROP TABLE IF EXISTS pull_request_commits CASCADE;
DROP TABLE IF EXISTS pull_requests CASCADE;
DROP TABLE IF EXISTS branch_protection_rules CASCADE;
DROP TABLE IF EXISTS branches CASCADE;
DROP TABLE IF EXISTS repositories CASCADE;
DROP TABLE IF EXISTS reviewers CASCADE;

CREATE TABLE repositories (
    repository_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE,
    default_branch text NOT NULL DEFAULT 'main',
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (length(trim(name)) >= 2),
    CHECK (default_branch ~ '^[A-Za-z0-9._/-]+$')
);

CREATE TABLE branches (
    branch_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id bigint NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_name text NOT NULL,
    head_sha text NOT NULL,
    protected boolean NOT NULL DEFAULT false,
    deleted_at timestamptz,
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) > 0),
    CHECK (length(trim(head_sha)) > 0)
);

CREATE TABLE reviewers (
    reviewer_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username text NOT NULL UNIQUE,
    active boolean NOT NULL DEFAULT true,
    can_approve boolean NOT NULL DEFAULT true,
    CHECK (length(trim(username)) > 0)
);

CREATE TABLE branch_protection_rules (
    protection_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id bigint NOT NULL UNIQUE REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    required_reviews integer NOT NULL DEFAULT 0,
    require_status_checks boolean NOT NULL DEFAULT true,
    restrict_direct_push boolean NOT NULL DEFAULT true,
    restrict_force_push boolean NOT NULL DEFAULT true,
    restrict_branch_deletion boolean NOT NULL DEFAULT true,
    require_conversation_resolution boolean NOT NULL DEFAULT true,
    require_linear_history boolean NOT NULL DEFAULT true,
    allow_admin_bypass boolean NOT NULL DEFAULT false,
    CHECK (required_reviews >= 0)
);

CREATE TYPE pull_request_state AS ENUM (
    'draft',
    'open',
    'closed',
    'merged'
);

CREATE TABLE pull_requests (
    pull_request_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id bigint NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    number integer NOT NULL,
    source_branch text NOT NULL,
    target_branch text NOT NULL,
    base_sha text NOT NULL,
    head_sha text NOT NULL,
    state pull_request_state NOT NULL DEFAULT 'open',
    unresolved_conversations integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (repository_id, number),
    CHECK (source_branch <> target_branch),
    CHECK (length(trim(base_sha)) > 0),
    CHECK (length(trim(head_sha)) > 0),
    CHECK (unresolved_conversations >= 0)
);

CREATE TABLE pull_request_commits (
    pull_request_id bigint NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    sequence_no integer NOT NULL,
    commit_sha text NOT NULL,
    commit_message text NOT NULL,
    PRIMARY KEY (pull_request_id, sequence_no),
    UNIQUE (pull_request_id, commit_sha),
    CHECK (sequence_no > 0),
    CHECK (length(trim(commit_sha)) > 0),
    CHECK (length(trim(commit_message)) > 0)
);

CREATE TYPE review_state AS ENUM (
    'commented',
    'changes_requested',
    'approved',
    'dismissed'
);

CREATE TABLE reviews (
    review_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id bigint NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id bigint NOT NULL REFERENCES reviewers(reviewer_id),
    state review_state NOT NULL,
    reviewed_head_sha text NOT NULL,
    submitted_at timestamptz NOT NULL DEFAULT now(),
    dismissed_at timestamptz,
    UNIQUE (pull_request_id, reviewer_id, submitted_at),
    CHECK (length(trim(reviewed_head_sha)) > 0),
    CHECK (
        (state = 'dismissed' AND dismissed_at IS NOT NULL)
        OR
        (state <> 'dismissed')
    )
);

CREATE TABLE review_comments (
    comment_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id bigint NOT NULL REFERENCES reviews(review_id)
        ON DELETE CASCADE,
    body text NOT NULL,
    file_path text,
    line_number integer,
    resolved boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (length(trim(body)) > 0),
    CHECK (line_number IS NULL OR line_number > 0)
);

CREATE TYPE check_state AS ENUM (
    'queued',
    'running',
    'passed',
    'failed'
);

CREATE TABLE status_checks (
    status_check_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id bigint NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name text NOT NULL,
    state check_state NOT NULL DEFAULT 'queued',
    commit_sha text NOT NULL,
    started_at timestamptz,
    completed_at timestamptz,
    failure_reason text,
    UNIQUE (pull_request_id, check_name, commit_sha),
    CHECK (length(trim(check_name)) > 0),
    CHECK (length(trim(commit_sha)) > 0),
    CHECK (
        completed_at IS NULL
        OR started_at IS NULL
        OR completed_at >= started_at
    )
);

CREATE INDEX idx_pr_repository_state
    ON pull_requests(repository_id, state);

CREATE INDEX idx_reviews_pr_state_head
    ON reviews(pull_request_id, state, reviewed_head_sha);

CREATE INDEX idx_status_checks_pr_state
    ON status_checks(pull_request_id, state);

CREATE INDEX idx_review_comments_unresolved
    ON review_comments(review_id)
    WHERE resolved = false;

INSERT INTO repositories (name, default_branch)
VALUES ('governance-platform', 'main');

INSERT INTO branches (
    repository_id,
    branch_name,
    head_sha,
    protected
)
SELECT repository_id, 'main', 'base-001', true
FROM repositories
WHERE name = 'governance-platform';

INSERT INTO branches (
    repository_id,
    branch_name,
    head_sha,
    protected
)
SELECT repository_id, 'feature/async-governance', 'pr-002', false
FROM repositories
WHERE name = 'governance-platform';

INSERT INTO reviewers (username, active, can_approve)
VALUES
    ('alice', true, true),
    ('bob', true, true),
    ('carol', true, false),
    ('former-reviewer', false, true);

INSERT INTO branch_protection_rules (
    branch_id,
    required_reviews,
    require_status_checks,
    restrict_direct_push,
    restrict_force_push,
    restrict_branch_deletion,
    require_conversation_resolution,
    require_linear_history,
    allow_admin_bypass
)
SELECT
    branch_id,
    2,
    true,
    true,
    true,
    true,
    true,
    true,
    false
FROM branches
WHERE branch_name = 'main';

INSERT INTO pull_requests (
    repository_id,
    number,
    source_branch,
    target_branch,
    base_sha,
    head_sha,
    state,
    unresolved_conversations
)
SELECT
    repository_id,
    17,
    'feature/async-governance',
    'main',
    'base-001',
    'pr-002',
    'open',
    1
FROM repositories
WHERE name = 'governance-platform';

INSERT INTO pull_request_commits (
    pull_request_id,
    sequence_no,
    commit_sha,
    commit_message
)
SELECT pull_request_id, 1, 'pr-001', 'Implement governance workflow'
FROM pull_requests
WHERE number = 17;

INSERT INTO pull_request_commits (
    pull_request_id,
    sequence_no,
    commit_sha,
    commit_message
)
SELECT pull_request_id, 2, 'pr-002', 'Add asynchronous status evaluation'
FROM pull_requests
WHERE number = 17;

-- Required CI jobs are separate rows because they may complete independently.
INSERT INTO status_checks (
    pull_request_id,
    check_name,
    state,
    commit_sha,
    started_at,
    completed_at
)
SELECT
    pull_request_id,
    check_name,
    state,
    'pr-002',
    started_at,
    completed_at
FROM pull_requests
CROSS JOIN (
    VALUES
        ('unit-tests', 'passed'::check_state),
        ('security-scan', 'passed'::check_state)
) AS checks(check_name, state)
WHERE number = 17;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    reviewed_head_sha
)
SELECT
    pr.pull_request_id,
    r.reviewer_id,
    'approved',
    pr.head_sha
FROM pull_requests pr
JOIN reviewers r
    ON r.username = 'alice'
WHERE pr.number = 17;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    reviewed_head_sha
)
SELECT
    pr.pull_request_id,
    r.reviewer_id,
    'approved',
    pr.head_sha
FROM pull_requests pr
JOIN reviewers r
    ON r.username = 'bob'
WHERE pr.number = 17;

INSERT INTO review_comments (
    review_id,
    body,
    file_path,
    line_number,
    resolved
)
SELECT
    review_id,
    'Clarify why status checks are evaluated independently.',
    'governance.js',
    84,
    false
FROM reviews
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE number = 17
)
LIMIT 1;

CREATE OR REPLACE FUNCTION set_review_timestamp()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.submitted_at := COALESCE(NEW.submitted_at, now());
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_review_timestamp
BEFORE INSERT ON reviews
FOR EACH ROW
EXECUTE FUNCTION set_review_timestamp();

CREATE OR REPLACE FUNCTION invalidate_stale_approvals()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    -- A new PR head invalidates approvals tied to the previous head.
    UPDATE reviews
    SET
        state = 'dismissed',
        dismissed_at = now()
    WHERE pull_request_id = NEW.pull_request_id
      AND state = 'approved'
      AND reviewed_head_sha <> NEW.head_sha;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_invalidate_stale_approvals
AFTER UPDATE OF head_sha ON pull_requests
FOR EACH ROW
WHEN (OLD.head_sha IS DISTINCT FROM NEW.head_sha)
EXECUTE FUNCTION invalidate_stale_approvals();

CREATE OR REPLACE FUNCTION evaluate_pull_request(
    requested_pull_request_id integer
)
RETURNS TABLE (
    pull_request_id bigint,
    eligible boolean,
    current_approvals bigint,
    required_approvals integer,
    failed_required_checks bigint,
    unresolved_conversations integer,
    reason text
)
LANGUAGE sql
AS $$
    WITH pr AS (
        SELECT
            p.pull_request_id,
            p.head_sha,
            p.state,
            p.unresolved_conversations,
            bpr.required_reviews,
            bpr.require_conversation_resolution
        FROM pull_requests p
        JOIN branches b
          ON b.repository_id = p.repository_id
         AND b.branch_name = p.target_branch
        JOIN branch_protection_rules bpr
          ON bpr.branch_id = b.branch_id
        WHERE p.pull_request_id = requested_pull_request_id
    ),
    approvals AS (
        SELECT
            r.pull_request_id,
            count(DISTINCT r.reviewer_id) AS current_approvals
        FROM reviews r
        JOIN pr
          ON pr.pull_request_id = r.pull_request_id
        JOIN reviewers rv
          ON rv.reviewer_id = r.reviewer_id
        WHERE r.state = 'approved'
          AND r.reviewed_head_sha = pr.head_sha
          AND rv.active
          AND rv.can_approve
        GROUP BY r.pull_request_id
    ),
    failed_checks AS (
        SELECT
            p.pull_request_id,
            count(*) AS failed_required_checks
        FROM pr p
        LEFT JOIN status_checks sc
          ON sc.pull_request_id = p.pull_request_id
         AND sc.commit_sha = p.head_sha
        WHERE sc.state IS DISTINCT FROM 'passed'
        GROUP BY p.pull_request_id
    )
    SELECT
        pr.pull_request_id,
        (
            pr.state = 'open'
            AND COALESCE(a.current_approvals, 0) >= pr.required_reviews
            AND COALESCE(fc.failed_required_checks, 0) = 0
            AND (
                NOT pr.require_conversation_resolution
                OR pr.unresolved_conversations = 0
            )
        ) AS eligible,
        COALESCE(a.current_approvals, 0),
        pr.required_reviews,
        COALESCE(fc.failed_required_checks, 0),
        pr.unresolved_conversations,
        CASE
            WHEN pr.state <> 'open'
                THEN 'Pull Request is not open'
            WHEN COALESCE(a.current_approvals, 0) < pr.required_reviews
                THEN 'Required current approvals are missing'
            WHEN COALESCE(fc.failed_required_checks, 0) > 0
                THEN 'Required status checks are incomplete or failed'
            WHEN pr.require_conversation_resolution
                 AND pr.unresolved_conversations > 0
                THEN 'Review conversations remain unresolved'
            ELSE 'Merge conditions satisfied'
        END
    FROM pr
    LEFT JOIN approvals a
      ON a.pull_request_id = pr.pull_request_id
    LEFT JOIN failed_checks fc
      ON fc.pull_request_id = pr.pull_request_id;
$$;

CREATE OR REPLACE VIEW merge_eligibility_report AS
SELECT *
FROM pull_requests p
CROSS JOIN LATERAL evaluate_pull_request(
    p.pull_request_id::integer
);

-- Demonstrate transactional state validation.
BEGIN;

SELECT *
FROM evaluate_pull_request(
    (
        SELECT pull_request_id::integer
        FROM pull_requests
        WHERE number = 17
    )
);

-- Resolve the review conversation only after its corresponding discussion
-- has actually been addressed.
UPDATE review_comments
SET resolved = true
WHERE review_id IN (
    SELECT review_id
    FROM reviews
    WHERE pull_request_id = (
        SELECT pull_request_id
        FROM pull_requests
        WHERE number = 17
    )
);

UPDATE pull_requests
SET
    unresolved_conversations = 0,
    updated_at = now()
WHERE number = 17;

SELECT *
FROM evaluate_pull_request(
    (
        SELECT pull_request_id::integer
        FROM pull_requests
        WHERE number = 17
    )
);

COMMIT;

-- Demonstrate stale approval behavior. The trigger automatically dismisses
-- approvals associated with the old head when the PR head changes.
BEGIN;

UPDATE pull_requests
SET
    head_sha = 'pr-003',
    updated_at = now()
WHERE number = 17;

INSERT INTO pull_request_commits (
    pull_request_id,
    sequence_no,
    commit_sha,
    commit_message
)
SELECT
    pull_request_id,
    3,
    'pr-003',
    'Synchronize base branch after review'
FROM pull_requests
WHERE number = 17;

SELECT
    reviewer_id,
    state,
    reviewed_head_sha,
    dismissed_at
FROM reviews
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE number = 17
);

ROLLBACK;

-- Reporting query: distinguish proposal state, review state,
-- approval freshness, asynchronous checks, and repository protection.
SELECT
    p.number AS pull_request,
    p.state,
    p.source_branch,
    p.target_branch,
    p.head_sha,
    bpr.required_reviews,
    COUNT(DISTINCT r.reviewer_id)
        FILTER (
            WHERE r.state = 'approved'
              AND r.reviewed_head_sha = p.head_sha
              AND rv.active
              AND rv.can_approve
        ) AS current_approvals,
    COUNT(*) FILTER (
        WHERE sc.state <> 'passed'
    ) AS incomplete_or_failed_checks,
    p.unresolved_conversations,
    (
        p.state = 'open'
        AND COUNT(DISTINCT r.reviewer_id)
            FILTER (
                WHERE r.state = 'approved'
                  AND r.reviewed_head_sha = p.head_sha
                  AND rv.active
                  AND rv.can_approve
            ) >= bpr.required_reviews
        AND COUNT(*) FILTER (
            WHERE sc.state <> 'passed'
        ) = 0
        AND (
            NOT bpr.require_conversation_resolution
            OR p.unresolved_conversations = 0
        )
    ) AS merge_eligible
FROM pull_requests p
JOIN branches b
  ON b.repository_id = p.repository_id
 AND b.branch_name = p.target_branch
JOIN branch_protection_rules bpr
  ON bpr.branch_id = b.branch_id
LEFT JOIN reviews r
  ON r.pull_request_id = p.pull_request_id
LEFT JOIN reviewers rv
  ON rv.reviewer_id = r.reviewer_id
LEFT JOIN status_checks sc
  ON sc.pull_request_id = p.pull_request_id
 AND sc.commit_sha = p.head_sha
GROUP BY
    p.pull_request_id,
    p.number,
    p.state,
    p.source_branch,
    p.target_branch,
    p.head_sha,
    bpr.required_reviews,
    bpr.require_conversation_resolution,
    p.unresolved_conversations
ORDER BY p.number;
