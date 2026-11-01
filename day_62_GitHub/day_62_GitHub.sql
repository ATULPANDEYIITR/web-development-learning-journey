DROP SCHEMA IF EXISTS github_workflow CASCADE;

CREATE SCHEMA github_workflow;

CREATE TYPE github_workflow.pr_state AS ENUM
    ('draft', 'open', 'closed', 'merged');

CREATE TYPE github_workflow.review_state AS ENUM
    ('commented', 'approved', 'changes_requested', 'dismissed');

CREATE TYPE github_workflow.check_state AS ENUM
    ('pending', 'passed', 'failed');

CREATE TYPE github_workflow.merge_strategy AS ENUM
    ('merge', 'squash', 'rebase');

CREATE TABLE github_workflow.users (
    user_id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE github_workflow.repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    owner_user_id BIGINT NOT NULL
        REFERENCES github_workflow.users(user_id),
    name TEXT NOT NULL,
    default_branch TEXT NOT NULL DEFAULT 'main',
    is_private BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (owner_user_id, name),
    CHECK (name ~ '^[A-Za-z0-9._-]+$')
);

CREATE TABLE github_workflow.branches (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES github_workflow.repositories(repository_id)
        ON DELETE CASCADE,
    name TEXT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    UNIQUE (repository_id, name),
    CHECK (name <> '')
);

CREATE TABLE github_workflow.commits (
    commit_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES github_workflow.repositories(repository_id)
        ON DELETE CASCADE,
    sha TEXT NOT NULL,
    author_user_id BIGINT NOT NULL
        REFERENCES github_workflow.users(user_id),
    message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repository_id, sha),
    CHECK (sha <> ''),
    CHECK (message <> '')
);

CREATE TABLE github_workflow.branch_commits (
    branch_id BIGINT NOT NULL
        REFERENCES github_workflow.branches(branch_id)
        ON DELETE CASCADE,
    commit_id BIGINT NOT NULL
        REFERENCES github_workflow.commits(commit_id)
        ON DELETE RESTRICT,
    position INTEGER NOT NULL,
    PRIMARY KEY (branch_id, commit_id),
    UNIQUE (branch_id, position),
    CHECK (position > 0)
);

CREATE TABLE github_workflow.issues (
    issue_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES github_workflow.repositories(repository_id)
        ON DELETE CASCADE,
    issue_number INTEGER NOT NULL,
    author_user_id BIGINT NOT NULL
        REFERENCES github_workflow.users(user_id),
    title TEXT NOT NULL,
    body TEXT,
    is_open BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repository_id, issue_number),
    CHECK (issue_number > 0),
    CHECK (title <> '')
);

CREATE TABLE github_workflow.pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES github_workflow.repositories(repository_id)
        ON DELETE CASCADE,
    pull_request_number INTEGER NOT NULL,
    source_branch_id BIGINT NOT NULL
        REFERENCES github_workflow.branches(branch_id),
    target_branch_id BIGINT NOT NULL
        REFERENCES github_workflow.branches(branch_id),
    author_user_id BIGINT NOT NULL
        REFERENCES github_workflow.users(user_id),
    title TEXT NOT NULL,
    state github_workflow.pr_state NOT NULL DEFAULT 'open',
    base_head_sha TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repository_id, pull_request_number),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (title <> '')
);

CREATE TABLE github_workflow.pull_request_commits (
    pull_request_id BIGINT NOT NULL
        REFERENCES github_workflow.pull_requests(pull_request_id)
        ON DELETE CASCADE,
    commit_id BIGINT NOT NULL
        REFERENCES github_workflow.commits(commit_id),
    position INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, position),
    CHECK (position > 0)
);

CREATE TABLE github_workflow.reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES github_workflow.pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_user_id BIGINT NOT NULL
        REFERENCES github_workflow.users(user_id),
    state github_workflow.review_state NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (review_id, pull_request_id)
);

CREATE TABLE github_workflow.review_comments (
    comment_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES github_workflow.pull_requests(pull_request_id)
        ON DELETE CASCADE,
    review_id BIGINT
        REFERENCES github_workflow.reviews(review_id)
        ON DELETE SET NULL,
    reviewer_user_id BIGINT NOT NULL
        REFERENCES github_workflow.users(user_id),
    file_path TEXT NOT NULL,
    line_number INTEGER,
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (file_path <> ''),
    CHECK (body <> ''),
    CHECK (line_number IS NULL OR line_number > 0)
);

CREATE TABLE github_workflow.status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES github_workflow.pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state github_workflow.check_state NOT NULL,
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE github_workflow.branch_protection (
    branch_id BIGINT PRIMARY KEY
        REFERENCES github_workflow.branches(branch_id)
        ON DELETE CASCADE,
    required_reviews INTEGER NOT NULL DEFAULT 1,
    dismiss_stale_approvals BOOLEAN NOT NULL DEFAULT TRUE,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (required_reviews >= 0)
);

CREATE TABLE github_workflow.required_checks (
    branch_id BIGINT NOT NULL
        REFERENCES github_workflow.branch_protection(branch_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (branch_id, check_name),
    CHECK (check_name <> '')
);

CREATE TABLE github_workflow.merge_events (
    merge_event_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES github_workflow.pull_requests(pull_request_id),
    merged_by_user_id BIGINT NOT NULL
        REFERENCES github_workflow.users(user_id),
    strategy github_workflow.merge_strategy NOT NULL,
    merged_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_branches_repository
    ON github_workflow.branches(repository_id);

CREATE INDEX idx_commits_repository_sha
    ON github_workflow.commits(repository_id, sha);

CREATE INDEX idx_pull_requests_target_state
    ON github_workflow.pull_requests(target_branch_id, state);

CREATE INDEX idx_reviews_pr_state
    ON github_workflow.reviews(pull_request_id, state);

CREATE INDEX idx_status_checks_pr_state
    ON github_workflow.status_checks(pull_request_id, state);

CREATE INDEX idx_comments_unresolved
    ON github_workflow.review_comments(pull_request_id, resolved)
    WHERE resolved = FALSE;

CREATE OR REPLACE FUNCTION github_workflow.prevent_self_approval()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    pr_author BIGINT;
BEGIN
    SELECT author_user_id
    INTO pr_author
    FROM github_workflow.pull_requests
    WHERE pull_request_id = NEW.pull_request_id;

    IF NEW.state = 'approved'
       AND NEW.reviewer_user_id = pr_author THEN
        RAISE EXCEPTION
            'Pull request author cannot approve their own pull request';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_self_approval
BEFORE INSERT OR UPDATE ON github_workflow.reviews
FOR EACH ROW
EXECUTE FUNCTION github_workflow.prevent_self_approval();

CREATE OR REPLACE FUNCTION github_workflow.touch_pull_request()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE github_workflow.pull_requests
    SET updated_at = CURRENT_TIMESTAMP
    WHERE pull_request_id = COALESCE(NEW.pull_request_id, OLD.pull_request_id);

    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER trg_review_updates_pr
AFTER INSERT OR UPDATE ON github_workflow.reviews
FOR EACH ROW
EXECUTE FUNCTION github_workflow.touch_pull_request();

CREATE TRIGGER trg_comment_updates_pr
AFTER INSERT OR UPDATE ON github_workflow.review_comments
FOR EACH ROW
EXECUTE FUNCTION github_workflow.touch_pull_request();

CREATE OR REPLACE FUNCTION github_workflow.merge_eligibility(
    p_pull_request_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_target_branch BIGINT;
    v_state github_workflow.pr_state;
    v_author BIGINT;
    v_required_reviews INTEGER;
    v_required_check_count INTEGER;
    v_failed_check_count INTEGER;
    v_approval_count INTEGER;
    v_unresolved_count INTEGER;
BEGIN
    SELECT
        pr.target_branch_id,
        pr.state,
        pr.author_user_id
    INTO
        v_target_branch,
        v_state,
        v_author
    FROM github_workflow.pull_requests pr
    WHERE pr.pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 'Pull request does not exist';
        RETURN;
    END IF;

    IF v_state <> 'open' THEN
        RETURN QUERY
        SELECT FALSE, 'Pull request is not open';
    END IF;

    SELECT COALESCE(bp.required_reviews, 0)
    INTO v_required_reviews
    FROM github_workflow.branch_protection bp
    WHERE bp.branch_id = v_target_branch;

    IF v_required_reviews IS NULL THEN
        v_required_reviews := 0;
    END IF;

    SELECT COUNT(DISTINCT reviewer_user_id)
    INTO v_approval_count
    FROM github_workflow.reviews
    WHERE pull_request_id = p_pull_request_id
      AND state = 'approved'
      AND reviewer_user_id <> v_author;

    IF v_approval_count < v_required_reviews THEN
        RETURN QUERY
        SELECT FALSE,
               format(
                   'Required approvals: %s; current approvals: %s',
                   v_required_reviews,
                   v_approval_count
               );
    END IF;

    SELECT COUNT(*)
    INTO v_required_check_count
    FROM github_workflow.required_checks
    WHERE branch_id = v_target_branch;

    SELECT COUNT(*)
    INTO v_failed_check_count
    FROM github_workflow.required_checks rc
    LEFT JOIN github_workflow.status_checks sc
      ON sc.pull_request_id = p_pull_request_id
     AND sc.check_name = rc.check_name
    WHERE rc.branch_id = v_target_branch
      AND (sc.status_check_id IS NULL OR sc.state <> 'passed');

    IF v_failed_check_count > 0 THEN
        RETURN QUERY
        SELECT FALSE,
               format(
                   '%s of %s required status checks are not passing',
                   v_failed_check_count,
                   v_required_check_count
               );
    END IF;

    SELECT COUNT(*)
    INTO v_unresolved_count
    FROM github_workflow.review_comments
    WHERE pull_request_id = p_pull_request_id
      AND resolved = FALSE;

    IF EXISTS (
        SELECT 1
        FROM github_workflow.branch_protection
        WHERE branch_id = v_target_branch
          AND require_conversation_resolution
          AND v_unresolved_count > 0
    ) THEN
        RETURN QUERY
        SELECT FALSE,
               format(
                   '%s unresolved review conversation(s)',
                   v_unresolved_count
               );
    END IF;

    IF EXISTS (
        SELECT 1
        FROM github_workflow.reviews
        WHERE pull_request_id = p_pull_request_id
          AND state = 'changes_requested'
    ) THEN
        RETURN QUERY
        SELECT FALSE, 'A reviewer has requested changes';
    END IF;

    RETURN QUERY
    SELECT TRUE, 'Pull request satisfies recorded merge conditions';
END;
$$;

CREATE OR REPLACE VIEW github_workflow.pull_request_status AS
SELECT
    pr.pull_request_id,
    r.name AS repository,
    pr.pull_request_number,
    pr.title,
    su.username AS source_branch,
    tu.username AS target_branch,
    author.username AS author,
    pr.state,
    COUNT(DISTINCT pc.commit_id) AS commit_count,
    COUNT(DISTINCT rv.review_id) AS review_count,
    COUNT(DISTINCT sc.status_check_id)
        FILTER (WHERE sc.state = 'passed') AS passing_checks,
    COUNT(DISTINCT rc.comment_id)
        FILTER (WHERE rc.resolved = FALSE) AS unresolved_comments
FROM github_workflow.pull_requests pr
JOIN github_workflow.repositories r
  ON r.repository_id = pr.repository_id
JOIN github_workflow.branches sb
  ON sb.branch_id = pr.source_branch_id
JOIN github_workflow.branches tb
  ON tb.branch_id = pr.target_branch_id
JOIN github_workflow.users su
  ON su.user_id = sb.repository_id
JOIN github_workflow.users tu
  ON tu.user_id = tb.repository_id
JOIN github_workflow.users author
  ON author.user_id = pr.author_user_id
LEFT JOIN github_workflow.pull_request_commits pc
  ON pc.pull_request_id = pr.pull_request_id
LEFT JOIN github_workflow.reviews rv
  ON rv.pull_request_id = pr.pull_request_id
LEFT JOIN github_workflow.status_checks sc
  ON sc.pull_request_id = pr.pull_request_id
LEFT JOIN github_workflow.review_comments rc
  ON rc.pull_request_id = pr.pull_request_id
GROUP BY
    pr.pull_request_id,
    r.name,
    pr.pull_request_number,
    pr.title,
    su.username,
    tu.username,
    author.username,
    pr.state;

INSERT INTO github_workflow.users
    (username, display_name)
VALUES
    ('alice', 'Alice Repository Owner'),
    ('bob', 'Bob Developer'),
    ('carol', 'Carol Reviewer'),
    ('david', 'David Security Reviewer'),
    ('eve', 'Eve Unauthorized Operator');

INSERT INTO github_workflow.repositories
    (owner_user_id, name, default_branch)
SELECT user_id, 'secure-service', 'main'
FROM github_workflow.users
WHERE username = 'alice';

INSERT INTO github_workflow.branches
    (repository_id, name)
SELECT repository_id, 'main'
FROM github_workflow.repositories
WHERE name = 'secure-service';

INSERT INTO github_workflow.branches
    (repository_id, name)
SELECT repository_id, 'feature/remote-workflow'
FROM github_workflow.repositories
WHERE name = 'secure-service';

INSERT INTO github_workflow.commits
    (repository_id, sha, author_user_id, message)
SELECT
    r.repository_id,
    'a1',
    u.user_id,
    'Initial repository implementation'
FROM github_workflow.repositories r
JOIN github_workflow.users u
  ON u.username = 'alice'
WHERE r.name = 'secure-service';

INSERT INTO github_workflow.commits
    (repository_id, sha, author_user_id, message)
SELECT
    r.repository_id,
    'b1',
    u.user_id,
    'Document clone pull push and README operations'
FROM github_workflow.repositories r
JOIN github_workflow.users u
  ON u.username = 'bob'
WHERE r.name = 'secure-service';

INSERT INTO github_workflow.commits
    (repository_id, sha, author_user_id, message)
SELECT
    r.repository_id,
    'b2',
    u.user_id,
    'Document issue workflow'
FROM github_workflow.repositories r
JOIN github_workflow.users u
  ON u.username = 'bob'
WHERE r.name = 'secure-service';

INSERT INTO github_workflow.branch_commits
    (branch_id, commit_id, position)
SELECT
    b.branch_id,
    c.commit_id,
    1
FROM github_workflow.branches b
JOIN github_workflow.commits c
  ON c.sha = 'a1'
WHERE b.name = 'main';

INSERT INTO github_workflow.branch_commits
    (branch_id, commit_id, position)
SELECT
    b.branch_id,
    c.commit_id,
    1
FROM github_workflow.branches b
JOIN github_workflow.commits c
  ON c.sha = 'a1'
WHERE b.name = 'feature/remote-workflow';

INSERT INTO github_workflow.branch_commits
    (branch_id, commit_id, position)
SELECT
    b.branch_id,
    c.commit_id,
    2
FROM github_workflow.branches b
JOIN github_workflow.commits c
  ON c.sha = 'b1'
WHERE b.name = 'feature/remote-workflow';

INSERT INTO github_workflow.branch_commits
    (branch_id, commit_id, position)
SELECT
    b.branch_id,
    c.commit_id,
    3
FROM github_workflow.branches b
JOIN github_workflow.commits c
  ON c.sha = 'b2'
WHERE b.name = 'feature/remote-workflow';

UPDATE github_workflow.branches
SET protected = TRUE
WHERE name = 'main';

INSERT INTO github_workflow.branch_protection
    (branch_id, required_reviews, dismiss_stale_approvals,
     require_conversation_resolution, allow_direct_push,
     allow_force_push, require_linear_history)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    TRUE
FROM github_workflow.branches
WHERE name = 'main';

INSERT INTO github_workflow.required_checks
    (branch_id, check_name)
SELECT branch_id, 'tests'
FROM github_workflow.branches
WHERE name = 'main';

INSERT INTO github_workflow.required_checks
    (branch_id, check_name)
SELECT branch_id, 'security-scan'
FROM github_workflow.branches
WHERE name = 'main';

INSERT INTO github_workflow.pull_requests
    (repository_id, pull_request_number, source_branch_id,
     target_branch_id, author_user_id, title, state, base_head_sha)
SELECT
    r.repository_id,
    1,
    sb.branch_id,
    tb.branch_id,
    u.user_id,
    'Document remote repository workflow',
    'open',
    'a1'
FROM github_workflow.repositories r
JOIN github_workflow.branches sb
  ON sb.repository_id = r.repository_id
 AND sb.name = 'feature/remote-workflow'
JOIN github_workflow.branches tb
  ON tb.repository_id = r.repository_id
 AND tb.name = 'main'
JOIN github_workflow.users u
  ON u.username = 'bob'
WHERE r.name = 'secure-service';

INSERT INTO github_workflow.pull_request_commits
    (pull_request_id, commit_id, position)
SELECT pr.pull_request_id, c.commit_id, 2
FROM github_workflow.pull_requests pr
JOIN github_workflow.commits c
  ON c.sha = 'b1'
WHERE pr.pull_request_number = 1;

INSERT INTO github_workflow.pull_request_commits
    (pull_request_id, commit_id, position)
SELECT pr.pull_request_id, c.commit_id, 3
FROM github_workflow.pull_requests pr
JOIN github_workflow.commits c
  ON c.sha = 'b2'
WHERE pr.pull_request_number = 1;

INSERT INTO github_workflow.reviews
    (pull_request_id, reviewer_user_id, state)
SELECT pr.pull_request_id, u.user_id, 'approved'
FROM github_workflow.pull_requests pr
JOIN github_workflow.users u
  ON u.username = 'carol'
WHERE pr.pull_request_number = 1;

INSERT INTO github_workflow.reviews
    (pull_request_id, reviewer_user_id, state)
SELECT pr.pull_request_id, u.user_id, 'approved'
FROM github_workflow.pull_requests pr
JOIN github_workflow.users u
  ON u.username = 'david'
WHERE pr.pull_request_number = 1;

INSERT INTO github_workflow.review_comments
    (pull_request_id, reviewer_user_id, file_path,
     line_number, body, resolved)
SELECT
    pr.pull_request_id,
    u.user_id,
    'README.md',
    42,
    'Clarify why protected branches reject direct pushes.',
    TRUE
FROM github_workflow.pull_requests pr
JOIN github_workflow.users u
  ON u.username = 'carol'
WHERE pr.pull_request_number = 1;

INSERT INTO github_workflow.status_checks
    (pull_request_id, check_name, state, completed_at)
SELECT
    pr.pull_request_id,
    'tests',
    'passed',
    CURRENT_TIMESTAMP
FROM github_workflow.pull_requests pr
WHERE pr.pull_request_number = 1;

INSERT INTO github_workflow.status_checks
    (pull_request_id, check_name, state, completed_at)
SELECT
    pr.pull_request_id,
    'security-scan',
    'passed',
    CURRENT_TIMESTAMP
FROM github_workflow.pull_requests pr
WHERE pr.pull_request_number = 1;

INSERT INTO github_workflow.issues
    (repository_id, issue_number, author_user_id, title, body)
SELECT
    r.repository_id,
    1,
    u.user_id,
    'Clarify clone, pull, push, README and issue workflow',
    'Document repository synchronization and issue-management behavior.'
FROM github_workflow.repositories r
JOIN github_workflow.users u
  ON u.username = 'alice'
WHERE r.name = 'secure-service';

SELECT *
FROM github_workflow.pull_request_status
ORDER BY pull_request_number;

SELECT *
FROM github_workflow.merge_eligibility(1);

SELECT
    r.name AS repository,
    COUNT(pr.pull_request_id) AS pull_requests,
    COUNT(*) FILTER (WHERE pr.state = 'merged') AS merged_pull_requests
FROM github_workflow.repositories r
LEFT JOIN github_workflow.pull_requests pr
  ON pr.repository_id = r.repository_id
GROUP BY r.repository_id, r.name;

SELECT
    u.username,
    COUNT(rv.review_id) AS reviews_submitted,
    COUNT(*) FILTER (WHERE rv.state = 'approved') AS approvals,
    COUNT(*) FILTER (WHERE rv.state = 'changes_requested')
        AS change_requests
FROM github_workflow.users u
LEFT JOIN github_workflow.reviews rv
  ON rv.reviewer_user_id = u.user_id
GROUP BY u.user_id, u.username
ORDER BY reviews_submitted DESC;

BEGIN;

UPDATE github_workflow.pull_requests
SET updated_at = CURRENT_TIMESTAMP
WHERE pull_request_number = 1
  AND state = 'open';

INSERT INTO github_workflow.merge_events
    (pull_request_id, merged_by_user_id, strategy)
SELECT
    pr.pull_request_id,
    u.user_id,
    'squash'
FROM github_workflow.pull_requests pr
JOIN github_workflow.users u
  ON u.username = 'alice'
WHERE pr.pull_request_number = 1
  AND EXISTS (
      SELECT 1
      FROM github_workflow.merge_eligibility(pr.pull_request_id)
      WHERE eligible = TRUE
  );

UPDATE github_workflow.pull_requests
SET state = 'merged',
    updated_at = CURRENT_TIMESTAMP
WHERE pull_request_number = 1
  AND EXISTS (
      SELECT 1
      FROM github_workflow.merge_events me
      WHERE me.pull_request_id = pull_requests.pull_request_id
  );

COMMIT;

SELECT
    pr.pull_request_number,
    pr.title,
    pr.state,
    me.strategy,
    me.merged_at
FROM github_workflow.pull_requests pr
LEFT JOIN github_workflow.merge_events me
  ON me.pull_request_id = pr.pull_request_id
ORDER BY pr.pull_request_number;
