DROP SCHEMA IF EXISTS repository_governance CASCADE;
CREATE SCHEMA repository_governance;
SET search_path TO repository_governance;

CREATE TYPE pull_request_state AS ENUM (
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

CREATE TYPE merge_strategy AS ENUM (
    'merge_commit',
    'squash',
    'rebase'
);

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE developers (
    developer_id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE repository_members (
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    developer_id BIGINT NOT NULL REFERENCES developers(developer_id)
        ON DELETE CASCADE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (repository_id, developer_id)
);

CREATE TABLE branches (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    head_sha CHAR(7),
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE commits (
    commit_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    sha CHAR(7) NOT NULL,
    message TEXT NOT NULL CHECK (length(trim(message)) > 0),
    author_id BIGINT NOT NULL REFERENCES developers(developer_id),
    committed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, sha)
);

CREATE TABLE pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    number INTEGER NOT NULL CHECK (number > 0),
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    state pull_request_state NOT NULL DEFAULT 'draft',
    merge_strategy merge_strategy NOT NULL DEFAULT 'squash',
    synchronized_with_base BOOLEAN NOT NULL DEFAULT TRUE,
    has_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    unresolved_conversations INTEGER NOT NULL DEFAULT 0
        CHECK (unresolved_conversations >= 0),
    created_by BIGINT NOT NULL REFERENCES developers(developer_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    merged_at TIMESTAMPTZ,
    UNIQUE (repository_id, number),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (
        state <> 'merged'
        OR merged_at IS NOT NULL
    )
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    commit_id BIGINT NOT NULL
        REFERENCES commits(commit_id)
        ON DELETE RESTRICT,
    position INTEGER NOT NULL CHECK (position > 0),
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, position)
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES developers(developer_id),
    state review_state NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE review_comments (
    comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(review_id)
        ON DELETE CASCADE,
    file_path TEXT NOT NULL CHECK (length(trim(file_path)) > 0),
    line_number INTEGER CHECK (line_number > 0),
    body TEXT NOT NULL CHECK (length(trim(body)) > 0),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL CHECK (length(trim(check_name)) > 0),
    passed BOOLEAN NOT NULL,
    required BOOLEAN NOT NULL DEFAULT TRUE,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection (
    branch_id BIGINT PRIMARY KEY REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    required_reviews INTEGER NOT NULL DEFAULT 0
        CHECK (required_reviews >= 0),
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    allow_admin_bypass BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE required_status_checks (
    branch_id BIGINT NOT NULL REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL CHECK (length(trim(check_name)) > 0),
    PRIMARY KEY (branch_id, check_name)
);

CREATE INDEX idx_pr_target_state
    ON pull_requests(target_branch_id, state);

CREATE INDEX idx_reviews_pr_state
    ON reviews(pull_request_id, state);

CREATE INDEX idx_status_checks_pr
    ON status_checks(pull_request_id, check_name);

CREATE OR REPLACE FUNCTION enforce_pull_request_repository()
RETURNS trigger
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
            'source, target, and pull request must belong to the same repository';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_enforce_pull_request_repository
BEFORE INSERT OR UPDATE ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION enforce_pull_request_repository();

CREATE OR REPLACE FUNCTION set_merge_timestamp()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.state = 'merged'
       AND OLD.state <> 'merged'
       AND NEW.merged_at IS NULL THEN
        NEW.merged_at := now();
    END IF;

    IF NEW.state <> 'merged' THEN
        NEW.merged_at := NULL;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_set_merge_timestamp
BEFORE UPDATE ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION set_merge_timestamp();

CREATE OR REPLACE VIEW pull_request_merge_eligibility AS
WITH approval_counts AS (
    SELECT
        pr.pull_request_id,
        count(*) FILTER (
            WHERE r.state = 'approved'
        ) AS approval_count,
        bool_or(r.state = 'changes_requested')
            AS has_requested_changes
    FROM pull_requests pr
    LEFT JOIN reviews r
        ON r.pull_request_id = pr.pull_request_id
    GROUP BY pr.pull_request_id
),
required_check_results AS (
    SELECT
        pr.pull_request_id,
        count(rsc.check_name) AS required_check_count,
        count(sc.check_name) FILTER (
            WHERE sc.passed = TRUE
        ) AS passed_required_check_count
    FROM pull_requests pr
    LEFT JOIN required_status_checks rsc
        ON rsc.branch_id = pr.target_branch_id
    LEFT JOIN status_checks sc
        ON sc.pull_request_id = pr.pull_request_id
       AND sc.check_name = rsc.check_name
    GROUP BY pr.pull_request_id
),
commit_counts AS (
    SELECT
        prc.pull_request_id,
        count(*) AS commit_count
    FROM pull_request_commits prc
    GROUP BY prc.pull_request_id
)
SELECT
    pr.pull_request_id,
    pr.repository_id,
    pr.number,
    pr.state,
    bp.required_reviews,
    COALESCE(ac.approval_count, 0) AS approval_count,
    COALESCE(cc.commit_count, 0) AS commit_count,
    COALESCE(ac.has_requested_changes, FALSE)
        AS has_requested_changes,
    pr.unresolved_conversations,
    pr.synchronized_with_base,
    pr.has_conflicts,
    COALESCE(rcr.required_check_count, 0)
        AS required_check_count,
    COALESCE(rcr.passed_required_check_count, 0)
        AS passed_required_check_count,
    (
        pr.state = 'open'
        AND COALESCE(cc.commit_count, 0) > 0
        AND pr.synchronized_with_base
        AND NOT pr.has_conflicts
        AND NOT COALESCE(ac.has_requested_changes, FALSE)
        AND COALESCE(ac.approval_count, 0) >= bp.required_reviews
        AND COALESCE(rcr.required_check_count, 0)
            = COALESCE(rcr.passed_required_check_count, 0)
        AND (
            NOT bp.require_conversation_resolution
            OR pr.unresolved_conversations = 0
        )
    ) AS mergeable
FROM pull_requests pr
JOIN branch_protection bp
    ON bp.branch_id = pr.target_branch_id
LEFT JOIN approval_counts ac
    ON ac.pull_request_id = pr.pull_request_id
LEFT JOIN required_check_results rcr
    ON rcr.pull_request_id = pr.pull_request_id
LEFT JOIN commit_counts cc
    ON cc.pull_request_id = pr.pull_request_id;

CREATE OR REPLACE FUNCTION merge_pull_request(
    p_pull_request_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    eligible BOOLEAN;
BEGIN
    SELECT mergeable
    INTO eligible
    FROM pull_request_merge_eligibility
    WHERE pull_request_id = p_pull_request_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'pull request % does not exist',
            p_pull_request_id;
    END IF;

    IF NOT eligible THEN
        RAISE EXCEPTION
            'pull request % does not satisfy merge policy',
            p_pull_request_id;
    END IF;

    UPDATE pull_requests
    SET state = 'merged'
    WHERE pull_request_id = p_pull_request_id;
END;
$$;

INSERT INTO repositories (name)
VALUES ('governance-engine');

INSERT INTO developers (username)
VALUES
    ('alice'),
    ('bob'),
    ('carol'),
    ('dave');

INSERT INTO repository_members (
    repository_id,
    developer_id,
    is_admin
)
SELECT
    r.repository_id,
    d.developer_id,
    CASE WHEN d.username = 'alice' THEN TRUE ELSE FALSE END
FROM repositories r
CROSS JOIN developers d;

INSERT INTO branches (
    repository_id,
    branch_name,
    head_sha,
    is_default
)
SELECT repository_id, 'main', 'a1b2c3d', TRUE
FROM repositories;

INSERT INTO branches (
    repository_id,
    branch_name,
    head_sha
)
SELECT repository_id, 'feature/governance', 'c3d4e5f'
FROM repositories;

INSERT INTO commits (
    repository_id,
    sha,
    message,
    author_id
)
SELECT
    r.repository_id,
    v.sha,
    v.message,
    d.developer_id
FROM repositories r
JOIN developers d ON d.username = 'alice'
CROSS JOIN (
    VALUES
        ('a1b2c3d', 'establish governance model'),
        ('b2c3d4e', 'implement merge eligibility'),
        ('c3d4e5f', 'resolve review policy')
) AS v(sha, message);

INSERT INTO branch_protection (
    branch_id,
    required_reviews,
    require_conversation_resolution,
    require_linear_history,
    allow_direct_push,
    allow_force_push,
    allow_deletion,
    allow_admin_bypass
)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    FALSE
FROM branches
WHERE branch_name = 'main';

INSERT INTO required_status_checks (
    branch_id,
    check_name
)
SELECT branch_id, check_name
FROM branches
CROSS JOIN (
    VALUES
        ('unit-tests'),
        ('security-scan')
) AS required(check_name)
WHERE branch_name = 'main';

INSERT INTO pull_requests (
    repository_id,
    number,
    source_branch_id,
    target_branch_id,
    state,
    merge_strategy,
    synchronized_with_base,
    has_conflicts,
    unresolved_conversations,
    created_by
)
SELECT
    r.repository_id,
    42,
    source.branch_id,
    target.branch_id,
    'open',
    'squash',
    TRUE,
    FALSE,
    2,
    d.developer_id
FROM repositories r
JOIN branches source
    ON source.repository_id = r.repository_id
   AND source.branch_name = 'feature/governance'
JOIN branches target
    ON target.repository_id = r.repository_id
   AND target.branch_name = 'main'
JOIN developers d
    ON d.username = 'alice';

INSERT INTO pull_request_commits (
    pull_request_id,
    commit_id,
    position
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    row_number() OVER (ORDER BY c.sha)
FROM pull_requests pr
JOIN commits c
    ON c.repository_id = pr.repository_id
WHERE pr.number = 42;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state
)
SELECT
    pr.pull_request_id,
    d.developer_id,
    'approved'
FROM pull_requests pr
JOIN developers d ON d.username = 'bob'
WHERE pr.number = 42;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state
)
SELECT
    pr.pull_request_id,
    d.developer_id,
    'commented'
FROM pull_requests pr
JOIN developers d ON d.username = 'carol'
WHERE pr.number = 42;

INSERT INTO review_comments (
    review_id,
    file_path,
    line_number,
    body,
    resolved
)
SELECT
    review_id,
    'governance.js',
    42,
    'Resolve this policy discussion before merging.',
    FALSE
FROM reviews
WHERE state = 'commented';

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    passed,
    required
)
SELECT
    pr.pull_request_id,
    checks.check_name,
    checks.passed,
    TRUE
FROM pull_requests pr
CROSS JOIN (
    VALUES
        ('unit-tests', TRUE),
        ('security-scan', FALSE)
) AS checks(check_name, passed)
WHERE pr.number = 42;

SELECT
    number,
    state,
    approval_count,
    required_reviews,
    commit_count,
    required_check_count,
    passed_required_check_count,
    unresolved_conversations,
    mergeable
FROM pull_request_merge_eligibility
ORDER BY number;

UPDATE pull_requests
SET unresolved_conversations = 0
WHERE number = 42;

UPDATE reviews
SET state = 'approved'
WHERE review_id = (
    SELECT r.review_id
    FROM reviews r
    JOIN pull_requests pr
        ON pr.pull_request_id = r.pull_request_id
    JOIN developers d
        ON d.developer_id = r.reviewer_id
    WHERE pr.number = 42
      AND d.username = 'carol'
    ORDER BY r.review_id DESC
    LIMIT 1
);

UPDATE status_checks
SET passed = TRUE
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE number = 42
)
AND check_name = 'security-scan';

SELECT
    number,
    mergeable,
    approval_count,
    required_reviews,
    unresolved_conversations,
    passed_required_check_count,
    required_check_count
FROM pull_request_merge_eligibility
WHERE number = 42;

BEGIN;

SELECT merge_pull_request(
    (
        SELECT pull_request_id
        FROM pull_requests
        WHERE number = 42
    )
);

COMMIT;

SELECT
    number,
    state,
    merged_at
FROM pull_requests
WHERE number = 42;

WITH review_quality AS (
    SELECT
        pr.number,
        count(r.review_id) AS review_count,
        count(*) FILTER (
            WHERE r.state = 'approved'
        ) AS approvals,
        count(*) FILTER (
            WHERE r.state = 'changes_requested'
        ) AS requested_changes
    FROM pull_requests pr
    LEFT JOIN reviews r
        ON r.pull_request_id = pr.pull_request_id
    GROUP BY pr.number
)
SELECT *
FROM review_quality
ORDER BY number;

SELECT
    b.branch_name,
    bp.required_reviews,
    bp.require_conversation_resolution,
    bp.require_linear_history,
    bp.allow_direct_push,
    bp.allow_force_push,
    bp.allow_deletion,
    bp.allow_admin_bypass
FROM branches b
JOIN branch_protection bp
    ON bp.branch_id = b.branch_id
WHERE b.is_default = TRUE;

-- The following transaction demonstrates database-level rollback.
BEGIN;

UPDATE pull_requests
SET state = 'closed'
WHERE number = 42;

ROLLBACK;

SELECT number, state
FROM pull_requests
WHERE number = 42;
