DROP SCHEMA IF EXISTS git_fundamentals CASCADE;
CREATE SCHEMA git_fundamentals;

SET search_path = git_fundamentals, public;

CREATE TYPE repository_state AS ENUM ('active', 'archived');
CREATE TYPE branch_state AS ENUM ('active', 'deleted');
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
CREATE TYPE check_state AS ENUM (
    'pending',
    'passed',
    'failed',
    'cancelled'
);
CREATE TYPE merge_strategy AS ENUM (
    'merge_commit',
    'squash',
    'rebase'
);

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    owner TEXT NOT NULL,
    state repository_state NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (owner, name),
    CHECK (name ~ '^[A-Za-z0-9._-]+$')
);

CREATE TABLE repository_members (
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY (repository_id, username),
    CHECK (role IN ('owner', 'maintainer', 'developer', 'reviewer'))
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    state branch_state NOT NULL DEFAULT 'active',
    head_commit_sha CHAR(40),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, branch_name),
    CHECK (
        branch_name ~ '^[A-Za-z0-9._/-]+$'
        AND branch_name NOT LIKE '/%'
        AND branch_name NOT LIKE '%/'
        AND branch_name NOT LIKE '%..%'
    )
);

CREATE TABLE commits (
    commit_sha CHAR(40) PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    author TEXT NOT NULL,
    committer TEXT NOT NULL,
    message TEXT NOT NULL,
    parent_sha CHAR(40),
    committed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (commit_sha ~ '^[0-9a-f]{40}$'),
    CHECK (length(trim(message)) > 0),
    FOREIGN KEY (parent_sha)
        REFERENCES commits(commit_sha)
);

ALTER TABLE branches
    ADD CONSTRAINT branches_head_commit_fk
    FOREIGN KEY (head_commit_sha)
    REFERENCES commits(commit_sha);

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    source_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    state pull_request_state NOT NULL DEFAULT 'open',
    author TEXT NOT NULL,
    source_head_sha CHAR(40) NOT NULL
        REFERENCES commits(commit_sha),
    target_base_sha CHAR(40) NOT NULL
        REFERENCES commits(commit_sha),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (length(trim(title)) > 0)
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    commit_sha CHAR(40) NOT NULL
        REFERENCES commits(commit_sha),
    sequence_no INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_sha),
    UNIQUE (pull_request_id, sequence_no),
    CHECK (sequence_no > 0)
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    reviewer TEXT NOT NULL,
    state review_state NOT NULL,
    commit_sha CHAR(40) NOT NULL
        REFERENCES commits(commit_sha),
    body TEXT NOT NULL DEFAULT '',
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES reviews(review_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(file_path)) > 0),
    CHECK (line_number IS NULL OR line_number > 0),
    CHECK (length(trim(body)) > 0)
);

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state check_state NOT NULL DEFAULT 'pending',
    commit_sha CHAR(40) NOT NULL
        REFERENCES commits(commit_sha),
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name, commit_sha)
);

CREATE TABLE branch_protection_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id) ON DELETE CASCADE,
    required_reviews INTEGER NOT NULL DEFAULT 0,
    require_status_checks BOOLEAN NOT NULL DEFAULT true,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT false,
    allow_direct_push BOOLEAN NOT NULL DEFAULT false,
    allow_force_push BOOLEAN NOT NULL DEFAULT false,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT false,
    require_linear_history BOOLEAN NOT NULL DEFAULT false,
    allow_admin_bypass BOOLEAN NOT NULL DEFAULT false,
    UNIQUE (repository_id, branch_id),
    CHECK (required_reviews >= 0)
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (policy_id, check_name)
);

CREATE TABLE approval_requirements (
    requirement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id) ON DELETE CASCADE,
    reviewer_username TEXT NOT NULL,
    UNIQUE (policy_id, reviewer_username)
);

CREATE INDEX idx_commits_repository_time
    ON commits(repository_id, committed_at DESC);

CREATE INDEX idx_pull_requests_target_state
    ON pull_requests(target_branch_id, state);

CREATE INDEX idx_reviews_pr_state
    ON reviews(pull_request_id, state);

CREATE INDEX idx_status_checks_pr_state
    ON status_checks(pull_request_id, state);

CREATE INDEX idx_comments_review_resolution
    ON review_comments(review_id, resolved);

CREATE OR REPLACE FUNCTION validate_pull_request_repository()
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
       OR source_repository <> NEW.repository_id
       OR target_repository <> NEW.repository_id THEN
        RAISE EXCEPTION
            'Pull Request branches must belong to the same repository';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_pull_request_repository
BEFORE INSERT OR UPDATE ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION validate_pull_request_repository();

CREATE OR REPLACE FUNCTION prevent_protected_branch_deletion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    protected BOOLEAN;
    deletion_allowed BOOLEAN;
BEGIN
    IF OLD.state = 'active' AND NEW.state = 'deleted' THEN
        SELECT EXISTS (
            SELECT 1
            FROM branch_protection_policies p
            WHERE p.branch_id = OLD.branch_id
        )
        INTO protected;

        IF protected THEN
            SELECT allow_branch_deletion
              INTO deletion_allowed
              FROM branch_protection_policies
             WHERE branch_id = OLD.branch_id;

            IF NOT deletion_allowed THEN
                RAISE EXCEPTION
                    'Protected branch % cannot be deleted',
                    OLD.branch_name;
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_protected_branch_deletion
BEFORE UPDATE OF state ON branches
FOR EACH ROW
EXECUTE FUNCTION prevent_protected_branch_deletion();

CREATE OR REPLACE FUNCTION merge_eligibility(
    requested_pr BIGINT
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
    approvals INTEGER;
    unresolved INTEGER;
    failed_checks INTEGER;
    missing_checks INTEGER;
BEGIN
    SELECT *
      INTO pr
      FROM pull_requests
     WHERE pull_request_id = requested_pr;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT false, 'Pull Request does not exist';
        RETURN;
    END IF;

    IF pr.state <> 'open' THEN
        RETURN QUERY
        SELECT false, 'Pull Request is not open';
        RETURN;
    END IF;

    SELECT p.*
      INTO policy
      FROM branch_protection_policies p
     WHERE p.branch_id = pr.target_branch_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT true, 'No branch protection policy applies';
        RETURN;
    END IF;

    SELECT count(*)
      INTO approvals
      FROM reviews r
     WHERE r.pull_request_id = pr.pull_request_id
       AND r.state = 'approved'
       AND r.commit_sha = pr.source_head_sha
       AND r.reviewer IN (
           SELECT reviewer_username
           FROM approval_requirements
           WHERE policy_id = policy.policy_id
       );

    IF approvals < policy.required_reviews THEN
        RETURN QUERY
        SELECT false,
               format(
                   'Required approvals: %, current eligible approvals: %',
                   policy.required_reviews,
                   approvals
               );
        RETURN;
    END IF;

    SELECT count(*)
      INTO unresolved
      FROM review_comments c
      JOIN reviews r ON r.review_id = c.review_id
     WHERE r.pull_request_id = pr.pull_request_id
       AND c.resolved = false;

    IF policy.require_conversation_resolution
       AND unresolved > 0 THEN
        RETURN QUERY
        SELECT false, 'Unresolved review conversations remain';
        RETURN;
    END IF;

    SELECT count(*)
      INTO failed_checks
      FROM status_checks s
     WHERE s.pull_request_id = pr.pull_request_id
       AND s.commit_sha = pr.source_head_sha
       AND s.state = 'failed';

    IF policy.require_status_checks AND failed_checks > 0 THEN
        RETURN QUERY
        SELECT false, 'At least one required status check failed';
        RETURN;
    END IF;

    SELECT count(*)
      INTO missing_checks
      FROM required_status_checks required
     WHERE required.policy_id = policy.policy_id
       AND NOT EXISTS (
           SELECT 1
           FROM status_checks actual
           WHERE actual.pull_request_id = pr.pull_request_id
             AND actual.commit_sha = pr.source_head_sha
             AND actual.check_name = required.check_name
             AND actual.state = 'passed'
       );

    IF policy.require_status_checks AND missing_checks > 0 THEN
        RETURN QUERY
        SELECT false, 'Required status checks are missing or not passed';
        RETURN;
    END IF;

    RETURN QUERY
    SELECT true, 'Pull Request satisfies the branch protection policy';
END;
$$;

CREATE VIEW pull_request_dashboard AS
SELECT
    pr.pull_request_id,
    r.owner || '/' || r.name AS repository,
    source.branch_name AS source_branch,
    target.branch_name AS target_branch,
    pr.title,
    pr.state,
    pr.author,
    pr.source_head_sha,
    count(DISTINCT rv.review_id) AS review_count,
    count(DISTINCT CASE
        WHEN rv.state = 'approved'
        THEN rv.review_id
    END) AS approval_count,
    count(DISTINCT CASE
        WHEN sc.state = 'passed'
        THEN sc.status_check_id
    END) AS passed_checks,
    count(DISTINCT CASE
        WHEN sc.state = 'failed'
        THEN sc.status_check_id
    END) AS failed_checks,
    count(DISTINCT c.comment_id)
        FILTER (WHERE c.resolved = false) AS unresolved_comments
FROM pull_requests pr
JOIN repositories r
  ON r.repository_id = pr.repository_id
JOIN branches source
  ON source.branch_id = pr.source_branch_id
JOIN branches target
  ON target.branch_id = pr.target_branch_id
LEFT JOIN reviews rv
  ON rv.pull_request_id = pr.pull_request_id
LEFT JOIN status_checks sc
  ON sc.pull_request_id = pr.pull_request_id
LEFT JOIN review_comments c
  ON c.review_id = rv.review_id
GROUP BY
    pr.pull_request_id,
    r.owner,
    r.name,
    source.branch_name,
    target.branch_name,
    pr.title,
    pr.state,
    pr.author,
    pr.source_head_sha;

INSERT INTO repositories (name, owner)
VALUES ('platform-service', 'acme');

INSERT INTO repository_members
    (repository_id, username, role)
VALUES
    (1, 'alice', 'owner'),
    (1, 'bob', 'maintainer'),
    (1, 'carol', 'reviewer'),
    (1, 'dave', 'reviewer');

INSERT INTO commits (
    commit_sha,
    repository_id,
    author,
    committer,
    message
)
VALUES
(
    repeat('1', 40),
    1,
    'alice',
    'alice',
    'Initial repository'
),
(
    repeat('2', 40),
    1,
    'alice',
    'alice',
    'Add deployment configuration'
),
(
    repeat('3', 40),
    1,
    'bob',
    'bob',
    'Implement audit logging'
);

INSERT INTO branches (
    repository_id,
    branch_name,
    head_commit_sha
)
VALUES
    (1, 'main', repeat('2', 40)),
    (1, 'feature/audit', repeat('3', 40));

INSERT INTO pull_requests (
    repository_id,
    source_branch_id,
    target_branch_id,
    title,
    description,
    author,
    source_head_sha,
    target_base_sha
)
VALUES (
    1,
    2,
    1,
    'Add audit logging',
    'Adds auditable application events.',
    'bob',
    repeat('3', 40),
    repeat('2', 40)
);

INSERT INTO pull_request_commits (
    pull_request_id,
    commit_sha,
    sequence_no
)
VALUES
    (1, repeat('3', 40), 1);

INSERT INTO branch_protection_policies (
    repository_id,
    branch_id,
    required_reviews,
    require_status_checks,
    require_conversation_resolution,
    allow_direct_push,
    allow_force_push,
    allow_branch_deletion,
    require_linear_history
)
VALUES (
    1,
    1,
    2,
    true,
    true,
    false,
    false,
    false,
    true
);

INSERT INTO approval_requirements (
    policy_id,
    reviewer_username
)
VALUES
    (1, 'carol'),
    (1, 'dave');

INSERT INTO required_status_checks (
    policy_id,
    check_name
)
VALUES
    (1, 'unit-tests'),
    (1, 'security-scan');

INSERT INTO reviews (
    pull_request_id,
    reviewer,
    state,
    commit_sha,
    body
)
VALUES
(
    1,
    'carol',
    'approved',
    repeat('3', 40),
    'Implementation meets the review criteria.'
),
(
    1,
    'dave',
    'approved',
    repeat('3', 40),
    'Security and operational behavior reviewed.'
);

INSERT INTO review_comments (
    review_id,
    file_path,
    line_number,
    body,
    resolved
)
VALUES
(
    1,
    'src/audit.py',
    42,
    'Please verify that the event identifier is unique.',
    true
);

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    state,
    commit_sha,
    completed_at
)
VALUES
(
    1,
    'unit-tests',
    'passed',
    repeat('3', 40),
    now()
),
(
    1,
    'security-scan',
    'passed',
    repeat('3', 40),
    now()
);

SELECT *
FROM pull_request_dashboard
ORDER BY pull_request_id;

SELECT *
FROM merge_eligibility(1);

WITH branch_commits AS (
    SELECT
        b.branch_name,
        c.commit_sha,
        c.message,
        c.committed_at
    FROM branches b
    JOIN commits c
      ON c.commit_sha = b.head_commit_sha
    WHERE b.repository_id = 1
)
SELECT *
FROM branch_commits
ORDER BY branch_name;

SELECT
    r.reviewer,
    count(*) AS review_count,
    count(*) FILTER (WHERE r.state = 'approved') AS approvals,
    count(*) FILTER (WHERE r.state = 'changes_requested')
        AS requested_changes
FROM reviews r
JOIN pull_requests pr
  ON pr.pull_request_id = r.pull_request_id
WHERE pr.repository_id = 1
GROUP BY r.reviewer
ORDER BY r.reviewer;

BEGIN;

UPDATE pull_requests
SET updated_at = now()
WHERE pull_request_id = 1
  AND state = 'open';

SELECT *
FROM merge_eligibility(1);

COMMIT;

BEGIN;

UPDATE branches
SET state = 'deleted'
WHERE branch_id = 1;

ROLLBACK;
