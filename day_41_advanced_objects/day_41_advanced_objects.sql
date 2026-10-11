-- PostgreSQL 15+
-- Advanced object concepts are represented as repository governance data.
-- The relational model enforces policy integrity; application-side object
-- descriptors and database constraints serve different purposes.

BEGIN;

DROP SCHEMA IF EXISTS repository_governance CASCADE;
CREATE SCHEMA repository_governance;
SET search_path TO repository_governance, public;

CREATE TYPE pull_request_state AS ENUM ('open', 'closed', 'merged');
CREATE TYPE review_state AS ENUM (
    'commented', 'approved', 'changes_requested', 'dismissed'
);
CREATE TYPE check_state AS ENUM ('pending', 'passed', 'failed');
CREATE TYPE merge_strategy AS ENUM ('merge_commit', 'squash', 'rebase');

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (position('/' IN full_name) > 1)
);

CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (username ~ '^[A-Za-z0-9][A-Za-z0-9-]{0,38}$')
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    head_commit CHAR(40) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name),
    CHECK (branch_name <> ''),
    CHECK (head_commit ~ '^[0-9a-f]{40}$')
);

CREATE TABLE branch_protection_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 1
        CHECK (required_approvals >= 0),
    require_code_owner BOOLEAN NOT NULL DEFAULT FALSE,
    require_checks BOOLEAN NOT NULL DEFAULT TRUE,
    require_resolved_conversations BOOLEAN NOT NULL DEFAULT TRUE,
    disallow_force_push BOOLEAN NOT NULL DEFAULT TRUE,
    disallow_deletion BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    dismiss_stale_approvals BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_push BOOLEAN NOT NULL DEFAULT TRUE,
    enforce_for_administrators BOOLEAN NOT NULL DEFAULT TRUE,
    allow_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    allowed_merge_strategies merge_strategy[] NOT NULL
        DEFAULT ARRAY['squash', 'rebase']::merge_strategy[],
    CHECK (cardinality(allowed_merge_strategies) > 0)
);

CREATE TABLE code_owners (
    branch_id BIGINT NOT NULL REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    PRIMARY KEY (branch_id, user_id)
);

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id)
        ON DELETE RESTRICT,
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id)
        ON DELETE RESTRICT,
    author_id BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    title TEXT NOT NULL,
    state pull_request_state NOT NULL DEFAULT 'open',
    is_draft BOOLEAN NOT NULL DEFAULT FALSE,
    has_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    conversations_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    current_head_commit CHAR(40) NOT NULL,
    reviewed_head_commit CHAR(40),
    merge_method merge_strategy,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ,
    CHECK (source_branch_id <> target_branch_id),
    CHECK (title <> ''),
    CHECK (current_head_commit ~ '^[0-9a-f]{40}$'),
    CHECK (
        reviewed_head_commit IS NULL
        OR reviewed_head_commit ~ '^[0-9a-f]{40}$'
    ),
    CHECK (
        (state = 'merged' AND merge_method IS NOT NULL)
        OR state <> 'merged'
    )
);

CREATE TABLE commits (
    commit_id CHAR(40) PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (commit_id ~ '^[0-9a-f]{40}$'),
    CHECK (message <> '')
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    commit_id CHAR(40) NOT NULL REFERENCES commits(commit_id)
        ON DELETE RESTRICT,
    position INTEGER NOT NULL CHECK (position >= 0),
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, position)
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    reviewed_head_commit CHAR(40) NOT NULL
        CHECK (reviewed_head_commit ~ '^[0-9a-f]{40}$'),
    state review_state NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    review_body TEXT NOT NULL DEFAULT ''
);

-- Multiple historical reviews are retained. The latest review per reviewer
-- determines the current decision rather than allowing an old approval to win.
CREATE INDEX reviews_latest_per_reviewer_idx
    ON reviews (pull_request_id, reviewer_id, submitted_at DESC, review_id DESC);

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(review_id)
        ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    is_inline BOOLEAN NOT NULL DEFAULT TRUE,
    body TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (file_path <> ''),
    CHECK (line_number IS NULL OR line_number > 0),
    CHECK (body <> ''),
    CHECK (NOT is_inline OR line_number IS NOT NULL)
);

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    head_commit CHAR(40) NOT NULL
        CHECK (head_commit ~ '^[0-9a-f]{40}$'),
    state check_state NOT NULL,
    completed_at TIMESTAMPTZ,
    details TEXT NOT NULL DEFAULT '',
    UNIQUE (pull_request_id, check_name, head_commit),
    CHECK (
        (state = 'pending' AND completed_at IS NULL)
        OR (state IN ('passed', 'failed') AND completed_at IS NOT NULL)
    )
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (policy_id, check_name),
    CHECK (check_name <> '')
);

CREATE TABLE merge_events (
    merge_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL UNIQUE
        REFERENCES pull_requests(pull_request_id)
        ON DELETE RESTRICT,
    merged_by BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    strategy merge_strategy NOT NULL,
    resulting_commit CHAR(40) NOT NULL
        CHECK (resulting_commit ~ '^[0-9a-f]{40}$'),
    merged_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX pull_requests_target_state_idx
    ON pull_requests (target_branch_id, state, created_at DESC);

CREATE INDEX status_checks_current_head_idx
    ON status_checks (pull_request_id, head_commit, check_name);

CREATE INDEX unresolved_comments_idx
    ON review_comments (review_id)
    WHERE is_resolved = FALSE;

-- A pull request's source and target branches must belong to its repository.
CREATE FUNCTION validate_pull_request_branches()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    source_repository BIGINT;
    target_repository BIGINT;
BEGIN
    SELECT repository_id INTO source_repository
    FROM branches
    WHERE branch_id = NEW.source_branch_id;

    SELECT repository_id INTO target_repository
    FROM branches
    WHERE branch_id = NEW.target_branch_id;

    IF source_repository IS DISTINCT FROM NEW.repository_id
       OR target_repository IS DISTINCT FROM NEW.repository_id THEN
        RAISE EXCEPTION 'Both Pull Request branches must belong to its repository';
    END IF;

    IF NEW.source_branch_id = NEW.target_branch_id THEN
        RAISE EXCEPTION 'Source and target branches must differ';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER pull_request_branch_integrity
BEFORE INSERT OR UPDATE OF repository_id, source_branch_id, target_branch_id
ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION validate_pull_request_branches();

-- The author cannot approve their own Pull Request.
CREATE FUNCTION prevent_self_approval()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    request_author BIGINT;
BEGIN
    SELECT author_id INTO request_author
    FROM pull_requests
    WHERE pull_request_id = NEW.pull_request_id;

    IF request_author = NEW.reviewer_id AND NEW.state = 'approved' THEN
        RAISE EXCEPTION 'Pull Request authors cannot approve their own changes';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER review_self_approval_guard
BEFORE INSERT OR UPDATE ON reviews
FOR EACH ROW
EXECUTE FUNCTION prevent_self_approval();

-- This function calculates current merge eligibility. It is a read-only policy
-- evaluator; an actual merge must lock rows and update Git refs transactionally
-- through the hosting service.
CREATE FUNCTION evaluate_merge_eligibility(request_id BIGINT)
RETURNS TABLE (
    pull_request_id BIGINT,
    eligible BOOLEAN,
    reasons TEXT[]
)
LANGUAGE sql
STABLE
AS $$
WITH request_context AS (
    SELECT
        pr.*,
        bp.policy_id,
        bp.required_approvals,
        bp.require_code_owner,
        bp.require_checks,
        bp.require_resolved_conversations,
        bp.dismiss_stale_approvals,
        bp.allowed_merge_strategies
    FROM pull_requests pr
    LEFT JOIN branch_protection_policies bp
        ON bp.branch_id = pr.target_branch_id
    WHERE pr.pull_request_id = request_id
),
latest_reviews AS (
    SELECT DISTINCT ON (r.reviewer_id)
        r.reviewer_id,
        r.state,
        r.reviewed_head_commit,
        r.pull_request_id
    FROM reviews r
    WHERE r.pull_request_id = request_id
    ORDER BY r.reviewer_id, r.submitted_at DESC, r.review_id DESC
),
approval_totals AS (
    SELECT
        COUNT(*) FILTER (
            WHERE lr.state = 'approved'
              AND (
                  NOT rc.dismiss_stale_approvals
                  OR lr.reviewed_head_commit = rc.current_head_commit
              )
        ) AS approval_count,
        BOOL_OR(
            lr.state = 'approved'
            AND co.user_id IS NOT NULL
            AND (
                NOT rc.dismiss_stale_approvals
                OR lr.reviewed_head_commit = rc.current_head_commit
            )
        ) AS has_code_owner_approval
    FROM request_context rc
    LEFT JOIN latest_reviews lr
        ON lr.pull_request_id = rc.pull_request_id
    LEFT JOIN code_owners co
        ON co.branch_id = rc.target_branch_id
       AND co.user_id = lr.reviewer_id
),
check_totals AS (
    SELECT
        COUNT(*) FILTER (
            WHERE rsc.check_name IS NULL
               OR sc.state IS DISTINCT FROM 'passed'
               OR sc.head_commit IS DISTINCT FROM rc.current_head_commit
        ) AS failing_or_missing_checks
    FROM request_context rc
    LEFT JOIN required_status_checks rsc
        ON rsc.policy_id = rc.policy_id
    LEFT JOIN LATERAL (
        SELECT s.state, s.head_commit
        FROM status_checks s
        WHERE s.pull_request_id = rc.pull_request_id
          AND s.check_name = rsc.check_name
          AND s.head_commit = rc.current_head_commit
        ORDER BY s.status_check_id DESC
        LIMIT 1
    ) sc ON TRUE
),
comment_totals AS (
    SELECT COUNT(*) AS unresolved_count
    FROM review_comments c
    JOIN reviews r ON r.review_id = c.review_id
    WHERE r.pull_request_id = request_id
      AND c.is_resolved = FALSE
)
SELECT
    rc.pull_request_id,
    (
        rc.state = 'open'
        AND NOT rc.is_draft
        AND NOT rc.has_conflicts
        AND rc.policy_id IS NOT NULL
        AND rc.target_branch_id <> rc.source_branch_id
        AND (
            NOT rc.require_resolved_conversations
            OR (
                rc.conversations_resolved
                AND ct.unresolved_count = 0
            )
        )
        AND at.approval_count >= rc.required_approvals
        AND (
            NOT rc.require_code_owner
            OR COALESCE(at.has_code_owner_approval, FALSE)
        )
        AND (
            NOT rc.require_checks
            OR cht.failing_or_missing_checks = 0
        )
    ) AS eligible,
    array_remove(ARRAY[
        CASE WHEN rc.state <> 'open'
            THEN 'Pull Request is not open' END,
        CASE WHEN rc.is_draft
            THEN 'Draft Pull Request cannot be merged' END,
        CASE WHEN rc.has_conflicts
            THEN 'Merge conflicts remain' END,
        CASE WHEN rc.policy_id IS NULL
            THEN 'Target branch has no protection policy' END,
        CASE WHEN rc.require_resolved_conversations
                  AND (NOT rc.conversations_resolved OR ct.unresolved_count > 0)
            THEN 'Review conversations remain unresolved' END,
        CASE WHEN at.approval_count < rc.required_approvals
            THEN 'Required current approvals are missing' END,
        CASE WHEN rc.require_code_owner
                  AND NOT COALESCE(at.has_code_owner_approval, FALSE)
            THEN 'Required code owner approval is missing' END,
        CASE WHEN rc.require_checks
                  AND cht.failing_or_missing_checks > 0
            THEN 'Required status checks are missing, pending, failed, or stale' END
    ], NULL) AS reasons
FROM request_context rc
CROSS JOIN approval_totals at
CROSS JOIN check_totals cht
CROSS JOIN comment_totals ct;
$$;

-- Sample repository, team, branches, and protected release policy.
INSERT INTO repositories (full_name, default_branch)
VALUES ('platform/inventory-service', 'main');

INSERT INTO users (username)
VALUES ('maya'), ('liam'), ('noah'), ('ops-admin');

INSERT INTO branches (repository_id, branch_name, head_commit)
SELECT repository_id, 'main', repeat('a', 40)
FROM repositories
WHERE full_name = 'platform/inventory-service';

INSERT INTO branches (repository_id, branch_name, head_commit)
SELECT repository_id, 'feature/audit-events', repeat('b', 40)
FROM repositories
WHERE full_name = 'platform/inventory-service';

INSERT INTO branches (repository_id, branch_name, head_commit)
SELECT repository_id, 'feature/retry-policy', repeat('c', 40)
FROM repositories
WHERE full_name = 'platform/inventory-service';

INSERT INTO branch_protection_policies (
    branch_id,
    required_approvals,
    require_code_owner,
    require_checks,
    require_resolved_conversations,
    disallow_force_push,
    disallow_deletion,
    require_linear_history,
    dismiss_stale_approvals,
    restrict_push,
    enforce_for_administrators,
    allow_bypass,
    allowed_merge_strategies
)
SELECT
    branch_id, 2, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE,
    TRUE, TRUE, FALSE, ARRAY['squash', 'rebase']::merge_strategy[]
FROM branches
WHERE branch_name = 'main';

INSERT INTO code_owners (branch_id, user_id)
SELECT b.branch_id, u.user_id
FROM branches b
JOIN users u ON u.username IN ('maya', 'liam')
WHERE b.branch_name = 'main';

INSERT INTO required_status_checks (policy_id, check_name)
SELECT policy_id, required_name
FROM branch_protection_policies
CROSS JOIN (VALUES ('ci'), ('security')) AS required(required_name);

INSERT INTO pull_requests (
    repository_id,
    source_branch_id,
    target_branch_id,
    author_id,
    title,
    is_draft,
    conversations_resolved,
    current_head_commit,
    reviewed_head_commit
)
SELECT
    r.repository_id,
    source.branch_id,
    target.branch_id,
    author.user_id,
    'Add audit event logging',
    FALSE,
    TRUE,
    repeat('b', 40),
    repeat('b', 40)
FROM repositories r
JOIN branches source
    ON source.repository_id = r.repository_id
   AND source.branch_name = 'feature/audit-events'
JOIN branches target
    ON target.repository_id = r.repository_id
   AND target.branch_name = 'main'
JOIN users author ON author.username = 'noah'
WHERE r.full_name = 'platform/inventory-service';

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    reviewed_head_commit,
    state,
    review_body
)
SELECT pr.pull_request_id, u.user_id, repeat('b', 40), 'approved',
       'Reviewed authorization and audit event handling.'
FROM pull_requests pr
CROSS JOIN users u
WHERE pr.title = 'Add audit event logging'
  AND u.username IN ('maya', 'liam');

INSERT INTO status_checks (
    pull_request_id, check_name, head_commit, state, completed_at
)
SELECT pr.pull_request_id, check_name, repeat('b', 40), 'passed', now()
FROM pull_requests pr
CROSS JOIN (VALUES ('ci'), ('security')) AS checks(check_name)
WHERE pr.title = 'Add audit event logging';

INSERT INTO review_comments (
    review_id, file_path, line_number, is_inline, body, is_resolved
)
SELECT
    review_id,
    'src/audit.py',
    42,
    TRUE,
    'Confirm that the event payload excludes credentials.',
    TRUE
FROM reviews
WHERE review_body = 'Reviewed authorization and audit event handling.'
LIMIT 1;

-- Inspect the current policy decision and any blocking reasons.
SELECT *
FROM evaluate_merge_eligibility(
    (SELECT pull_request_id
     FROM pull_requests
     WHERE title = 'Add audit event logging')
);

-- Inspect policy configuration without changing it.
SELECT
    b.branch_name,
    p.required_approvals,
    p.require_code_owner,
    p.require_checks,
    p.require_resolved_conversations,
    p.disallow_force_push,
    p.disallow_deletion,
    p.require_linear_history,
    p.dismiss_stale_approvals,
    p.restrict_push,
    p.enforce_for_administrators,
    p.allow_bypass,
    p.allowed_merge_strategies
FROM branch_protection_policies p
JOIN branches b ON b.branch_id = p.branch_id;

-- Latest reviewer decisions distinguish current approval state from history.
SELECT DISTINCT ON (u.username)
    u.username,
    r.state,
    r.reviewed_head_commit,
    r.submitted_at
FROM reviews r
JOIN users u ON u.user_id = r.reviewer_id
WHERE r.pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE title = 'Add audit event logging'
)
ORDER BY u.username, r.submitted_at DESC, r.review_id DESC;

-- Transaction rollback demonstrates that failed governance operations need not
-- leave partial state changes. This intentionally invalid update is caught
-- inside a savepoint so the rest of the demonstration can proceed.
SAVEPOINT invalid_policy_change;

DO $$
BEGIN
    UPDATE branch_protection_policies
    SET required_approvals = -1
    WHERE branch_id = (
        SELECT branch_id FROM branches WHERE branch_name = 'main'
    );
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'Rejected negative approval threshold.';
END;
$$;

ROLLBACK TO SAVEPOINT invalid_policy_change;
RELEASE SAVEPOINT invalid_policy_change;

COMMIT;
