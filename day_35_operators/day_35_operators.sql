-- PostgreSQL 15+ compatible
-- Operator-focused repository governance model.
--
-- SQL does not have JavaScript's ?. or ?? operators. Their closest
-- database-level equivalents are explicit NULL-safe expressions such as
-- COALESCE, NULLIF, CASE, and JSON operators. This script demonstrates
-- those mechanisms alongside arithmetic, comparison, logical, assignment-
-- like UPDATE operations, constraints, transactions, and policy queries.

DROP SCHEMA IF EXISTS operator_governance CASCADE;
CREATE SCHEMA operator_governance;
SET search_path TO operator_governance;

CREATE TYPE review_state AS ENUM (
    'PENDING',
    'APPROVED',
    'CHANGES_REQUESTED',
    'COMMENTED'
);

CREATE TYPE check_state AS ENUM (
    'PENDING',
    'PASSED',
    'FAILED'
);

CREATE TYPE merge_strategy AS ENUM (
    'MERGE_COMMIT',
    'SQUASH',
    'REBASE'
);

CREATE TABLE repository (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_name TEXT NOT NULL,
    repository_name TEXT NOT NULL,
    default_branch TEXT NOT NULL DEFAULT 'main',
    UNIQUE (owner_name, repository_name),
    CHECK (length(trim(owner_name)) > 0),
    CHECK (length(trim(repository_name)) > 0)
);

CREATE TABLE branch (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) > 0)
);

CREATE TABLE reviewer (
    reviewer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    eligible_to_approve BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE pull_request (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    source_branch_id BIGINT NOT NULL REFERENCES branch(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branch(branch_id),
    pull_request_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    additions INTEGER NOT NULL DEFAULT 0,
    deletions INTEGER NOT NULL DEFAULT 0,
    is_draft BOOLEAN NOT NULL DEFAULT TRUE,
    is_mergeable BOOLEAN NOT NULL DEFAULT TRUE,
    merge_strategy merge_strategy,
    UNIQUE (repository_id, pull_request_number),
    CHECK (pull_request_number > 0),
    CHECK (additions >= 0),
    CHECK (deletions >= 0),
    CHECK (source_branch_id <> target_branch_id)
);

CREATE TABLE commit_record (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    commit_hash CHAR(40) NOT NULL UNIQUE,
    commit_message TEXT NOT NULL,
    authored_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (commit_hash ~ '^[0-9a-f]{40}$')
);

CREATE TABLE review (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES reviewer(reviewer_id),
    state review_state NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE review_comment (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES review(review_id)
        ON DELETE CASCADE,
    body TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(body)) > 0)
);

CREATE TABLE status_check (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state check_state NOT NULL DEFAULT 'PENDING',
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection_policy (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES branch(branch_id)
        ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 1,
    maximum_changed_lines INTEGER NOT NULL DEFAULT 500,
    require_passing_checks BOOLEAN NOT NULL DEFAULT TRUE,
    require_resolved_conversations BOOLEAN NOT NULL DEFAULT TRUE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (required_approvals >= 0),
    CHECK (maximum_changed_lines > 0)
);

CREATE INDEX idx_pull_request_target
    ON pull_request(target_branch_id, is_draft, is_mergeable);

CREATE INDEX idx_review_pr_state
    ON review(pull_request_id, state);

CREATE INDEX idx_review_comment_unresolved
    ON review_comment(review_id)
    WHERE is_resolved = FALSE;

CREATE INDEX idx_status_check_pr_state
    ON status_check(pull_request_id, state);

INSERT INTO repository (owner_name, repository_name)
VALUES ('example-org', 'governed-payments');

INSERT INTO branch (repository_id, branch_name, is_protected)
SELECT repository_id, 'main', TRUE
FROM repository
WHERE repository_name = 'governed-payments';

INSERT INTO branch (repository_id, branch_name, is_protected)
SELECT repository_id, 'feature/payment-timeout', FALSE
FROM repository
WHERE repository_name = 'governed-payments';

INSERT INTO branch (repository_id, branch_name, is_protected)
SELECT repository_id, 'feature/audit-log', FALSE
FROM repository
WHERE repository_name = 'governed-payments';

INSERT INTO reviewer (username, eligible_to_approve, active)
VALUES
    ('alice', TRUE, TRUE),
    ('bob', TRUE, TRUE),
    ('external-contributor', FALSE, TRUE),
    ('former-reviewer', TRUE, FALSE);

INSERT INTO branch_protection_policy (
    branch_id,
    required_approvals,
    maximum_changed_lines,
    require_passing_checks,
    require_resolved_conversations,
    allow_direct_push,
    allow_force_push,
    allow_branch_deletion,
    require_linear_history
)
SELECT
    branch_id,
    2,
    500,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    TRUE
FROM branch
WHERE branch_name = 'main';

INSERT INTO pull_request (
    repository_id,
    source_branch_id,
    target_branch_id,
    pull_request_number,
    title,
    additions,
    deletions,
    is_draft,
    is_mergeable,
    merge_strategy
)
SELECT
    r.repository_id,
    source.branch_id,
    target.branch_id,
    301,
    'Increase payment timeout handling',
    140,
    60,
    FALSE,
    TRUE,
    'SQUASH'
FROM repository r
JOIN branch source
    ON source.repository_id = r.repository_id
    AND source.branch_name = 'feature/payment-timeout'
JOIN branch target
    ON target.repository_id = r.repository_id
    AND target.branch_name = 'main'
WHERE r.repository_name = 'governed-payments';

INSERT INTO pull_request (
    repository_id,
    source_branch_id,
    target_branch_id,
    pull_request_number,
    title,
    additions,
    deletions,
    is_draft,
    is_mergeable,
    merge_strategy
)
SELECT
    r.repository_id,
    source.branch_id,
    target.branch_id,
    302,
    'Add audit logging',
    60,
    30,
    FALSE,
    TRUE,
    'MERGE_COMMIT'
FROM repository r
JOIN branch source
    ON source.repository_id = r.repository_id
    AND source.branch_name = 'feature/audit-log'
JOIN branch target
    ON target.repository_id = r.repository_id
    AND target.branch_name = 'main'
WHERE r.repository_name = 'governed-payments';

INSERT INTO review (pull_request_id, reviewer_id, state)
SELECT pr.pull_request_id, rv.reviewer_id, 'APPROVED'
FROM pull_request pr
JOIN reviewer rv ON rv.username = 'alice'
WHERE pr.pull_request_number = 301;

INSERT INTO review (pull_request_id, reviewer_id, state)
SELECT pr.pull_request_id, rv.reviewer_id, 'APPROVED'
FROM pull_request pr
JOIN reviewer rv ON rv.username = 'bob'
WHERE pr.pull_request_number = 301;

INSERT INTO review (pull_request_id, reviewer_id, state)
SELECT pr.pull_request_id, rv.reviewer_id, 'APPROVED'
FROM pull_request pr
JOIN reviewer rv ON rv.username = 'external-contributor'
WHERE pr.pull_request_number = 301;

INSERT INTO review (pull_request_id, reviewer_id, state)
SELECT pr.pull_request_id, rv.reviewer_id, 'APPROVED'
FROM pull_request pr
JOIN reviewer rv ON rv.username = 'alice'
WHERE pr.pull_request_number = 302;

INSERT INTO review (pull_request_id, reviewer_id, state)
SELECT pr.pull_request_id, rv.reviewer_id, 'CHANGES_REQUESTED'
FROM pull_request pr
JOIN reviewer rv ON rv.username = 'bob'
WHERE pr.pull_request_number = 302;

INSERT INTO review_comment (review_id, body, is_resolved)
SELECT
    review_id,
    'Retention policy needs review.',
    FALSE
FROM review
JOIN pull_request
    ON pull_request.pull_request_id = review.pull_request_id
WHERE pull_request.pull_request_number = 302
  AND state = 'CHANGES_REQUESTED';

INSERT INTO status_check (pull_request_id, check_name, state, completed_at)
SELECT pull_request_id, check_name, 'PASSED', CURRENT_TIMESTAMP
FROM pull_request
CROSS JOIN (
    VALUES
        ('build'),
        ('unit-tests'),
        ('security-scan')
) AS checks(check_name)
WHERE pull_request_number = 301;

INSERT INTO status_check (pull_request_id, check_name, state, completed_at)
SELECT pull_request_id, check_name, 'PASSED', CURRENT_TIMESTAMP
FROM pull_request
CROSS JOIN (
    VALUES
        ('build'),
        ('unit-tests'),
        ('security-scan')
) AS checks(check_name)
WHERE pull_request_number = 302;

-- Arithmetic and comparison operators calculate the effective change size.
SELECT
    pull_request_number,
    additions,
    deletions,
    additions + deletions AS changed_lines,
    (additions + deletions) <= 500 AS within_default_limit
FROM pull_request
ORDER BY pull_request_number;

-- Logical operators combine independent policy conditions.
SELECT
    pr.pull_request_number,
    pr.is_draft = FALSE AS not_draft,
    pr.is_mergeable = TRUE AS mergeable,
    COUNT(*) FILTER (
        WHERE rv.eligible_to_approve
          AND rv.active
          AND r.state = 'APPROVED'
    ) >= bp.required_approvals AS enough_approvals,
    BOOL_AND(sc.state = 'PASSED') AS checks_pass,
    (
        NOT bp.require_resolved_conversations
        OR COUNT(rc.comment_id) FILTER (
            WHERE rc.is_resolved = FALSE
        ) = 0
    ) AS conversations_pass,
    (
        pr.is_draft = FALSE
        AND pr.is_mergeable = TRUE
        AND COUNT(*) FILTER (
            WHERE rv.eligible_to_approve
              AND rv.active
              AND r.state = 'APPROVED'
        ) >= bp.required_approvals
        AND BOOL_AND(sc.state = 'PASSED')
        AND (
            NOT bp.require_resolved_conversations
            OR COUNT(rc.comment_id) FILTER (
                WHERE rc.is_resolved = FALSE
            ) = 0
        )
    ) AS merge_eligible
FROM pull_request pr
JOIN branch_protection_policy bp
    ON bp.branch_id = pr.target_branch_id
JOIN review r
    ON r.pull_request_id = pr.pull_request_id
JOIN reviewer rv
    ON rv.reviewer_id = r.reviewer_id
JOIN status_check sc
    ON sc.pull_request_id = pr.pull_request_id
LEFT JOIN review_comment rc
    ON rc.review_id = r.review_id
GROUP BY
    pr.pull_request_number,
    pr.is_draft,
    pr.is_mergeable,
    bp.required_approvals,
    bp.require_resolved_conversations;

-- CASE is SQL's conditional expression and provides ternary-style behavior.
SELECT
    pull_request_number,
    CASE
        WHEN is_draft THEN 'DRAFT'
        WHEN is_mergeable THEN 'READY'
        ELSE 'CONFLICTED'
    END AS lifecycle_state
FROM pull_request
ORDER BY pull_request_number;

-- COALESCE is the SQL equivalent of choosing the first non-NULL value.
SELECT
    repository_name,
    COALESCE(default_branch, 'main') AS effective_default_branch
FROM repository;

-- NULLIF converts a value into NULL when it matches another value.
-- It is useful when an application would otherwise divide by zero.
SELECT
    10.0 / NULLIF(2, 0) AS safe_division,
    10.0 / NULLIF(0, 0) AS division_that_becomes_null;

-- PostgreSQL JSON operators provide safe access to structured metadata.
ALTER TABLE pull_request
ADD COLUMN metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

UPDATE pull_request
SET metadata = jsonb_build_object(
    'risk', CASE
        WHEN additions + deletions > 300 THEN 'high'
        ELSE 'normal'
    END,
    'team', 'payments'
);

SELECT
    pull_request_number,
    metadata ->> 'risk' AS risk_level,
    COALESCE(metadata ->> 'team', 'unassigned') AS owning_team
FROM pull_request;

-- UPDATE demonstrates assignment at the relational data layer.
UPDATE pull_request
SET is_draft = FALSE
WHERE pull_request_number = 301
  AND is_draft = TRUE;

-- Transactional workflow: resolve the blocking discussion and re-evaluate.
BEGIN;

UPDATE review_comment
SET is_resolved = TRUE
WHERE comment_id IN (
    SELECT rc.comment_id
    FROM review_comment rc
    JOIN review r
        ON r.review_id = rc.review_id
    JOIN pull_request pr
        ON pr.pull_request_id = r.pull_request_id
    WHERE pr.pull_request_number = 302
      AND rc.is_resolved = FALSE
);

COMMIT;

-- Final governance report.
WITH approval_counts AS (
    SELECT
        pr.pull_request_id,
        COUNT(*) FILTER (
            WHERE rv.eligible_to_approve
              AND rv.active
              AND r.state = 'APPROVED'
        ) AS approvals
    FROM pull_request pr
    LEFT JOIN review r
        ON r.pull_request_id = pr.pull_request_id
    LEFT JOIN reviewer rv
        ON rv.reviewer_id = r.reviewer_id
    GROUP BY pr.pull_request_id
),
check_results AS (
    SELECT
        pull_request_id,
        COUNT(*) AS check_count,
        COUNT(*) FILTER (WHERE state = 'PASSED') AS passed_checks
    FROM status_check
    GROUP BY pull_request_id
),
conversation_results AS (
    SELECT
        r.pull_request_id,
        COUNT(rc.comment_id)
            FILTER (WHERE rc.is_resolved = FALSE) AS unresolved_comments
    FROM review r
    LEFT JOIN review_comment rc
        ON rc.review_id = r.review_id
    GROUP BY r.pull_request_id
)
SELECT
    pr.pull_request_number,
    ac.approvals,
    bp.required_approvals,
    pr.additions + pr.deletions AS changed_lines,
    bp.maximum_changed_lines,
    cr.check_count,
    cr.passed_checks,
    COALESCE(cvr.unresolved_comments, 0) AS unresolved_comments,
    CASE
        WHEN pr.is_draft THEN 'BLOCKED: draft'
        WHEN NOT pr.is_mergeable THEN 'BLOCKED: conflict'
        WHEN ac.approvals < bp.required_approvals
            THEN 'BLOCKED: approvals'
        WHEN pr.additions + pr.deletions > bp.maximum_changed_lines
            THEN 'BLOCKED: size'
        WHEN bp.require_passing_checks
             AND COALESCE(cr.check_count, 0) = 0
            THEN 'BLOCKED: no checks'
        WHEN bp.require_passing_checks
             AND cr.passed_checks <> cr.check_count
            THEN 'BLOCKED: failed checks'
        WHEN bp.require_resolved_conversations
             AND COALESCE(cvr.unresolved_comments, 0) > 0
            THEN 'BLOCKED: unresolved discussion'
        ELSE 'MERGE ELIGIBLE'
    END AS governance_decision
FROM pull_request pr
JOIN branch_protection_policy bp
    ON bp.branch_id = pr.target_branch_id
JOIN approval_counts ac
    ON ac.pull_request_id = pr.pull_request_id
LEFT JOIN check_results cr
    ON cr.pull_request_id = pr.pull_request_id
LEFT JOIN conversation_results cvr
    ON cvr.pull_request_id = pr.pull_request_id
ORDER BY pr.pull_request_number;
