DROP SCHEMA IF EXISTS git_advanced CASCADE;
CREATE SCHEMA git_advanced;
SET search_path TO git_advanced;

CREATE TYPE branch_kind AS ENUM ('main', 'feature', 'release', 'hotfix');
CREATE TYPE commit_kind AS ENUM ('normal', 'merge', 'revert');
CREATE TYPE review_state AS ENUM ('pending', 'approved', 'changes_requested', 'commented', 'dismissed');
CREATE TYPE check_state AS ENUM ('pending', 'passed', 'failed', 'cancelled');
CREATE TYPE merge_strategy AS ENUM ('merge_commit', 'squash', 'fast_forward', 'rebase');

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL DEFAULT 'main',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (name ~ '^[A-Za-z0-9._-]+$')
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    kind branch_kind NOT NULL,
    head_commit_id BIGINT,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, name)
);

CREATE TABLE commits (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id) ON DELETE CASCADE,
    commit_hash TEXT NOT NULL UNIQUE,
    message TEXT NOT NULL,
    kind commit_kind NOT NULL DEFAULT 'normal',
    author TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(message)) >= 3),
    CHECK (commit_hash ~ '^[0-9a-f]{8,64}$')
);

CREATE TABLE commit_parents (
    commit_id BIGINT NOT NULL REFERENCES commits(commit_id) ON DELETE CASCADE,
    parent_commit_id BIGINT NOT NULL REFERENCES commits(commit_id),
    parent_position INTEGER NOT NULL CHECK (parent_position > 0),
    PRIMARY KEY (commit_id, parent_position),
    UNIQUE (commit_id, parent_commit_id),
    CHECK (commit_id <> parent_commit_id)
);

ALTER TABLE branches
    ADD CONSTRAINT fk_branch_head
    FOREIGN KEY (head_commit_id) REFERENCES commits(commit_id);

CREATE TABLE repository_tags (
    tag_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    commit_id BIGINT NOT NULL REFERENCES commits(commit_id),
    annotated_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, name),
    CHECK (name ~ '^[A-Za-z0-9._/-]+$')
);

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id) ON DELETE CASCADE,
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('draft', 'open', 'merged', 'closed')),
    source_head_commit_id BIGINT REFERENCES commits(commit_id),
    target_base_commit_id BIGINT REFERENCES commits(commit_id),
    merge_strategy merge_strategy,
    merged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (length(trim(title)) >= 5),
    CHECK (
        (status = 'merged' AND merge_strategy IS NOT NULL AND merged_at IS NOT NULL)
        OR status <> 'merged'
    )
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    commit_id BIGINT NOT NULL REFERENCES commits(commit_id),
    sequence_no INTEGER NOT NULL CHECK (sequence_no > 0),
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, sequence_no)
);

CREATE TABLE developers (
    developer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (username ~ '^[A-Za-z0-9_.-]+$')
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES developers(developer_id),
    state review_state NOT NULL,
    body TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    dismissed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, reviewer_id, submitted_at)
);

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(body)) >= 2)
);

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state check_state NOT NULL DEFAULT 'pending',
    commit_id BIGINT REFERENCES commits(commit_id),
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id) ON DELETE CASCADE,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES branches(branch_id) ON DELETE CASCADE,
    required_reviews INTEGER NOT NULL DEFAULT 1 CHECK (required_reviews >= 0),
    require_status_checks BOOLEAN NOT NULL DEFAULT TRUE,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    required_merge_strategy merge_strategy,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_commits_repository_time
    ON commits(repository_id, committed_at DESC);

CREATE INDEX idx_reviews_pr_state
    ON reviews(pull_request_id, state);

CREATE INDEX idx_status_checks_pr_state
    ON status_checks(pull_request_id, state);

CREATE INDEX idx_comments_review_resolved
    ON review_comments(review_id, resolved);

CREATE INDEX idx_pr_target_status
    ON pull_requests(target_branch_id, status);

CREATE OR REPLACE FUNCTION prevent_protected_direct_push()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    is_protected BOOLEAN;
    direct_push_allowed BOOLEAN;
BEGIN
    SELECT b.protected, COALESCE(bp.allow_direct_push, FALSE)
    INTO is_protected, direct_push_allowed
    FROM branches b
    LEFT JOIN branch_protection bp ON bp.branch_id = b.branch_id
    WHERE b.branch_id = NEW.branch_id;

    IF is_protected AND NOT direct_push_allowed THEN
        IF OLD.head_commit_id IS DISTINCT FROM NEW.head_commit_id THEN
            RAISE EXCEPTION 'Direct update rejected for protected branch %', NEW.name;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_protected_direct_push
BEFORE UPDATE OF head_commit_id ON branches
FOR EACH ROW
EXECUTE FUNCTION prevent_protected_direct_push();

CREATE OR REPLACE FUNCTION unresolved_conversations(
    p_pull_request_id BIGINT
)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT count(*)::INTEGER
    FROM review_comments rc
    JOIN reviews r ON r.review_id = rc.review_id
    WHERE r.pull_request_id = p_pull_request_id
      AND NOT rc.resolved;
$$;

CREATE OR REPLACE FUNCTION approved_reviewer_count(
    p_pull_request_id BIGINT
)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT count(DISTINCT reviewer_id)::INTEGER
    FROM reviews
    WHERE pull_request_id = p_pull_request_id
      AND state = 'approved'
      AND dismissed_at IS NULL;
$$;

CREATE OR REPLACE FUNCTION failed_status_check_count(
    p_pull_request_id BIGINT
)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT count(*)::INTEGER
    FROM status_checks
    WHERE pull_request_id = p_pull_request_id
      AND state IN ('failed', 'cancelled');
$$;

CREATE OR REPLACE FUNCTION merge_eligibility(
    p_pull_request_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    approvals_ok BOOLEAN,
    checks_ok BOOLEAN,
    conversations_ok BOOLEAN,
    branch_policy_ok BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    pr RECORD;
    policy RECORD;
    approval_count INTEGER;
    unresolved INTEGER;
    failed_checks INTEGER;
    pending_checks INTEGER;
BEGIN
    SELECT *
    INTO pr
    FROM pull_requests
    WHERE pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, FALSE, FALSE, FALSE, FALSE, 'Pull Request not found';
        RETURN;
    END IF;

    SELECT *
    INTO policy
    FROM branch_protection
    WHERE branch_id = pr.target_branch_id;

    approval_count := approved_reviewer_count(p_pull_request_id);
    unresolved := unresolved_conversations(p_pull_request_id);
    failed_checks := failed_status_check_count(p_pull_request_id);

    SELECT count(*)
    INTO pending_checks
    FROM status_checks
    WHERE pull_request_id = p_pull_request_id
      AND state = 'pending';

    approvals_ok :=
        policy IS NULL
        OR approval_count >= policy.required_reviews;

    checks_ok :=
        policy IS NULL
        OR NOT policy.require_status_checks
        OR (failed_checks = 0 AND pending_checks = 0);

    conversations_ok :=
        policy IS NULL
        OR NOT policy.require_conversation_resolution
        OR unresolved = 0;

    branch_policy_ok :=
        policy IS NULL
        OR (
            policy.required_merge_strategy IS NULL
            OR pr.merge_strategy = policy.required_merge_strategy
        );

    eligible :=
        pr.status IN ('open', 'draft')
        AND approvals_ok
        AND checks_ok
        AND conversations_ok
        AND branch_policy_ok;

    reason :=
        CASE
            WHEN pr.status NOT IN ('open', 'draft')
                THEN 'Pull Request is not open'
            WHEN NOT approvals_ok
                THEN 'Required approvals are missing'
            WHEN NOT checks_ok
                THEN 'Required status checks are not passing'
            WHEN NOT conversations_ok
                THEN 'Unresolved review conversations remain'
            WHEN NOT branch_policy_ok
                THEN 'Merge strategy violates branch policy'
            ELSE 'Eligible for merge'
        END;

    RETURN QUERY
    SELECT
        merge_eligibility.eligible,
        merge_eligibility.approvals_ok,
        merge_eligibility.checks_ok,
        merge_eligibility.conversations_ok,
        merge_eligibility.branch_policy_ok,
        merge_eligibility.reason;
END;
$$;

CREATE OR REPLACE PROCEDURE merge_pull_request(
    p_pull_request_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    eligibility RECORD;
BEGIN
    PERFORM pg_advisory_xact_lock(p_pull_request_id);

    SELECT *
    INTO eligibility
    FROM merge_eligibility(p_pull_request_id);

    IF NOT eligibility.eligible THEN
        RAISE EXCEPTION 'Pull Request % cannot be merged: %',
            p_pull_request_id,
            eligibility.reason;
    END IF;

    UPDATE pull_requests
    SET status = 'merged',
        merged_at = now()
    WHERE pull_request_id = p_pull_request_id;
END;
$$;

INSERT INTO repositories (name, default_branch)
VALUES ('platform-api', 'main');

INSERT INTO developers (username, email)
VALUES
    ('alice', 'alice@example.test'),
    ('bob', 'bob@example.test'),
    ('carol', 'carol@example.test');

INSERT INTO commits (
    repository_id,
    commit_hash,
    message,
    kind,
    author
)
SELECT
    repository_id,
    'a1000001',
    'Initial application',
    'normal',
    'alice'
FROM repositories
WHERE name = 'platform-api';

INSERT INTO commits (
    repository_id,
    commit_hash,
    message,
    kind,
    author
)
SELECT
    repository_id,
    'b2000002',
    'Add caching layer',
    'normal',
    'bob'
FROM repositories
WHERE name = 'platform-api';

INSERT INTO commits (
    repository_id,
    commit_hash,
    message,
    kind,
    author
)
SELECT
    repository_id,
    'c3000003',
    'Document deployment',
    'normal',
    'carol'
FROM repositories
WHERE name = 'platform-api';

INSERT INTO commit_parents (commit_id, parent_commit_id, parent_position)
SELECT c2.commit_id, c1.commit_id, 1
FROM commits c1
JOIN commits c2 ON c2.commit_hash = 'b2000002'
WHERE c1.commit_hash = 'a1000001';

INSERT INTO commit_parents (commit_id, parent_commit_id, parent_position)
SELECT c3.commit_id, c1.commit_id, 1
FROM commits c1
JOIN commits c3 ON c3.commit_hash = 'c3000003'
WHERE c1.commit_hash = 'a1000001';

INSERT INTO branches (
    repository_id,
    name,
    kind,
    head_commit_id,
    protected
)
SELECT
    r.repository_id,
    'main',
    'main',
    c.commit_id,
    TRUE
FROM repositories r
JOIN commits c ON c.commit_hash = 'a1000001'
WHERE r.name = 'platform-api';

INSERT INTO branches (
    repository_id,
    name,
    kind,
    head_commit_id,
    protected
)
SELECT
    r.repository_id,
    'feature/cache',
    'feature',
    c.commit_id,
    FALSE
FROM repositories r
JOIN commits c ON c.commit_hash = 'b2000002'
WHERE r.name = 'platform-api';

UPDATE repositories
SET default_branch = 'main'
WHERE name = 'platform-api';

INSERT INTO branch_protection (
    repository_id,
    branch_id,
    required_reviews,
    require_status_checks,
    require_conversation_resolution,
    allow_force_push,
    allow_branch_deletion,
    allow_direct_push,
    require_linear_history,
    required_merge_strategy
)
SELECT
    r.repository_id,
    b.branch_id,
    2,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    FALSE,
    'merge_commit'
FROM repositories r
JOIN branches b
  ON b.repository_id = r.repository_id
 AND b.name = 'main'
WHERE r.name = 'platform-api';

INSERT INTO pull_requests (
    repository_id,
    source_branch_id,
    target_branch_id,
    title,
    status,
    source_head_commit_id,
    target_base_commit_id,
    merge_strategy
)
SELECT
    r.repository_id,
    source.branch_id,
    target.branch_id,
    'Add production cache',
    'open',
    source.head_commit_id,
    target.head_commit_id,
    'merge_commit'
FROM repositories r
JOIN branches source
  ON source.repository_id = r.repository_id
 AND source.name = 'feature/cache'
JOIN branches target
  ON target.repository_id = r.repository_id
 AND target.name = 'main'
WHERE r.name = 'platform-api';

INSERT INTO pull_request_commits (pull_request_id, commit_id, sequence_no)
SELECT
    pr.pull_request_id,
    c.commit_id,
    1
FROM pull_requests pr
JOIN commits c ON c.commit_hash = 'b2000002'
WHERE pr.title = 'Add production cache';

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    body
)
SELECT
    pr.pull_request_id,
    d.developer_id,
    'approved',
    'Reviewed cache implementation'
FROM pull_requests pr
JOIN developers d ON d.username = 'alice'
WHERE pr.title = 'Add production cache';

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    body
)
SELECT
    pr.pull_request_id,
    d.developer_id,
    'approved',
    'Reviewed deployment impact'
FROM pull_requests pr
JOIN developers d ON d.username = 'carol'
WHERE pr.title = 'Add production cache';

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    state,
    commit_id,
    completed_at
)
SELECT
    pull_request_id,
    'unit-tests',
    'passed',
    source_head_commit_id,
    now()
FROM pull_requests
WHERE title = 'Add production cache';

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    state,
    commit_id,
    completed_at
)
SELECT
    pull_request_id,
    'security-scan',
    'passed',
    source_head_commit_id,
    now()
FROM pull_requests
WHERE title = 'Add production cache';

-- Retrieval: repository branches and their current commits.
SELECT
    r.name AS repository,
    b.name AS branch,
    b.kind,
    c.commit_hash,
    c.message
FROM repositories r
JOIN branches b ON b.repository_id = r.repository_id
LEFT JOIN commits c ON c.commit_id = b.head_commit_id
ORDER BY r.name, b.name;

-- Evaluation: current merge eligibility.
SELECT
    pr.pull_request_id,
    pr.title,
    e.eligible,
    e.approvals_ok,
    e.checks_ok,
    e.conversations_ok,
    e.branch_policy_ok,
    e.reason
FROM pull_requests pr
CROSS JOIN LATERAL merge_eligibility(pr.pull_request_id) e;

-- Aggregation: review decisions per Pull Request.
SELECT
    pr.pull_request_id,
    pr.title,
    count(*) FILTER (WHERE r.state = 'approved') AS approvals,
    count(*) FILTER (WHERE r.state = 'changes_requested') AS changes_requested
FROM pull_requests pr
LEFT JOIN reviews r ON r.pull_request_id = pr.pull_request_id
GROUP BY pr.pull_request_id, pr.title;

-- Workflow reporting: status-check state by Pull Request.
SELECT
    pr.title,
    sc.check_name,
    sc.state
FROM pull_requests pr
JOIN status_checks sc ON sc.pull_request_id = pr.pull_request_id
ORDER BY pr.pull_request_id, sc.check_name;

-- Transactional merge. The advisory lock prevents two concurrent merge
-- attempts for the same Pull Request from passing the policy check together.
BEGIN;
CALL merge_pull_request(
    (SELECT pull_request_id
     FROM pull_requests
     WHERE title = 'Add production cache')
);
COMMIT;

-- Release tagging is represented as a database-level immutable association.
INSERT INTO repository_tags (
    repository_id,
    name,
    commit_id,
    annotated_message
)
SELECT
    r.repository_id,
    'v1.0.0',
    b.head_commit_id,
    'First production release'
FROM repositories r
JOIN branches b
  ON b.repository_id = r.repository_id
WHERE r.name = 'platform-api'
  AND b.name = 'main';

-- Final reporting of merged Pull Requests and release tags.
SELECT
    pr.pull_request_id,
    pr.title,
    pr.status,
    pr.merge_strategy,
    pr.merged_at
FROM pull_requests pr
ORDER BY pr.pull_request_id;

SELECT
    r.name AS repository,
    t.name AS tag,
    c.commit_hash,
    c.message
FROM repository_tags t
JOIN repositories r ON r.repository_id = t.repository_id
JOIN commits c ON c.commit_id = t.commit_id;
