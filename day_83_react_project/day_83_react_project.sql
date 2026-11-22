-- ============================================================
-- PRODUCTION-STYLE ADMIN DASHBOARD
-- Repository Governance Database
-- PostgreSQL 15+
--
-- Features:
-- Repositories, branches, commits, Pull Requests, code reviews,
-- approval policies, status checks, conversations, merge
-- eligibility, merge history, audit logging and reporting.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS repository_admin;

SET search_path TO repository_admin, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE pr_state AS ENUM (
    'draft',
    'open',
    'closed',
    'merged'
);

CREATE TYPE review_state AS ENUM (
    'approved',
    'changes_requested',
    'commented',
    'dismissed'
);

CREATE TYPE check_state AS ENUM (
    'pending',
    'success',
    'failure',
    'cancelled'
);

CREATE TYPE actor_role AS ENUM (
    'developer',
    'reviewer',
    'maintainer',
    'administrator',
    'ci_system'
);

CREATE TYPE merge_strategy AS ENUM (
    'merge_commit',
    'squash',
    'rebase'
);

-- ============================================================
-- 2. USERS AND REPOSITORIES
-- ============================================================

CREATE TABLE actors (
    actor_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    role actor_role NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    owner_id BIGINT NOT NULL REFERENCES actors(actor_id),
    visibility VARCHAR(20) NOT NULL DEFAULT 'private',
    default_branch VARCHAR(150) NOT NULL DEFAULT 'main',
    archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(owner_id, name),
    CHECK (visibility IN ('private', 'public', 'internal'))
);

CREATE TABLE repository_members (
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    actor_id BIGINT NOT NULL
        REFERENCES actors(actor_id) ON DELETE CASCADE,
    member_role VARCHAR(30) NOT NULL,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(repository_id, actor_id),
    CHECK (
        member_role IN (
            'read',
            'triage',
            'write',
            'maintain',
            'admin'
        )
    )
);

-- ============================================================
-- 3. COMMITS AND BRANCHES
-- ============================================================

CREATE TABLE commits (
    commit_id VARCHAR(64) PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES actors(actor_id),
    message TEXT NOT NULL,
    parent_commit_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(repository_id, commit_id),

    FOREIGN KEY(repository_id, parent_commit_id)
        REFERENCES commits(repository_id, commit_id),

    CHECK (commit_id ~ '^[a-fA-F0-9]{12,64}$'),
    CHECK (LENGTH(TRIM(message)) > 0)
);

CREATE INDEX idx_commits_repository_created
    ON commits(repository_id, created_at DESC);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    head_commit_id VARCHAR(64) NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(repository_id, name),

    FOREIGN KEY(repository_id, head_commit_id)
        REFERENCES commits(repository_id, commit_id)
);

CREATE INDEX idx_branches_active
    ON branches(repository_id, name)
    WHERE deleted_at IS NULL;

-- ============================================================
-- 4. BRANCH PROTECTION POLICIES
-- ============================================================

CREATE TABLE branch_protection_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE
        REFERENCES branches(branch_id) ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 2,
    require_resolved_conversations BOOLEAN NOT NULL DEFAULT TRUE,
    require_up_to_date BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT TRUE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    allow_admin_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    enforce_stale_approval_dismissal BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (required_approvals BETWEEN 0 AND 100)
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id) ON DELETE CASCADE,
    check_name VARCHAR(100) NOT NULL,
    PRIMARY KEY(policy_id, check_name)
);

-- ============================================================
-- 5. PULL REQUESTS
-- ============================================================

CREATE TABLE pull_requests (
    pr_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id),
    author_id BIGINT NOT NULL REFERENCES actors(actor_id),
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    title VARCHAR(250) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    state pr_state NOT NULL DEFAULT 'open',
    base_commit_id VARCHAR(64) NOT NULL,
    head_commit_id VARCHAR(64) NOT NULL,
    is_draft BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    merged_at TIMESTAMPTZ,

    FOREIGN KEY(repository_id, base_commit_id)
        REFERENCES commits(repository_id, commit_id),

    FOREIGN KEY(repository_id, head_commit_id)
        REFERENCES commits(repository_id, commit_id),

    CHECK (source_branch_id <> target_branch_id),
    CHECK (LENGTH(TRIM(title)) > 0),
    CHECK (
        (state = 'draft' AND is_draft = TRUE)
        OR
        (state <> 'draft' AND is_draft = FALSE)
    )
);

CREATE INDEX idx_pr_repository_state
    ON pull_requests(repository_id, state, updated_at DESC);

CREATE INDEX idx_pr_author
    ON pull_requests(author_id, created_at DESC);

CREATE INDEX idx_pr_target
    ON pull_requests(target_branch_id, state);

-- ============================================================
-- 6. REVIEW REQUESTS AND CODE REVIEWS
-- ============================================================

CREATE TABLE review_requests (
    pr_id BIGINT NOT NULL
        REFERENCES pull_requests(pr_id) ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES actors(actor_id),
    requested_by BIGINT NOT NULL REFERENCES actors(actor_id),
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(pr_id, reviewer_id)
);

CREATE TABLE code_reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id BIGINT NOT NULL
        REFERENCES pull_requests(pr_id) ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES actors(actor_id),
    decision review_state NOT NULL,
    reviewed_commit_id VARCHAR(64) NOT NULL,
    review_comment TEXT NOT NULL DEFAULT '',
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(pr_id, reviewer_id),

    FOREIGN KEY(
        (SELECT NULL)
    ) REFERENCES actors(actor_id)
);

-- The reviewer decision is stored separately from the discussion.
CREATE INDEX idx_reviews_pr_decision
    ON code_reviews(pr_id, decision);

CREATE INDEX idx_reviews_reviewer
    ON code_reviews(reviewer_id, submitted_at DESC);

-- ============================================================
-- 7. REVIEW COMMENTS AND CONVERSATIONS
-- ============================================================

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id BIGINT NOT NULL
        REFERENCES pull_requests(pr_id) ON DELETE CASCADE,
    review_id BIGINT REFERENCES code_reviews(review_id),
    author_id BIGINT NOT NULL REFERENCES actors(actor_id),
    file_path TEXT NOT NULL,
    line_number INTEGER,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by BIGINT REFERENCES actors(actor_id),
    resolved_at TIMESTAMPTZ,

    CHECK (line_number IS NULL OR line_number > 0),
    CHECK (LENGTH(TRIM(body)) > 0),
    CHECK (
        (resolved = FALSE AND resolved_at IS NULL)
        OR
        (resolved = TRUE AND resolved_at IS NOT NULL)
    )
);

CREATE INDEX idx_comments_unresolved
    ON review_comments(pr_id)
    WHERE resolved = FALSE;

-- ============================================================
-- 8. AUTOMATED STATUS CHECKS
-- ============================================================

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id BIGINT NOT NULL
        REFERENCES pull_requests(pr_id) ON DELETE CASCADE,
    check_name VARCHAR(100) NOT NULL,
    status check_state NOT NULL DEFAULT 'pending',
    commit_id VARCHAR(64) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    details TEXT NOT NULL DEFAULT '',

    CHECK (
        (status = 'pending' AND completed_at IS NULL)
        OR
        (status <> 'pending' AND completed_at IS NOT NULL)
    )
);

CREATE INDEX idx_status_checks_pr_name
    ON status_checks(pr_id, check_name, started_at DESC);

-- ============================================================
-- 9. MERGE HISTORY AND AUDIT EVENTS
-- ============================================================

CREATE TABLE merge_history (
    merge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id BIGINT NOT NULL UNIQUE
        REFERENCES pull_requests(pr_id),
    merged_by BIGINT NOT NULL REFERENCES actors(actor_id),
    merge_commit_id VARCHAR(64) NOT NULL,
    strategy merge_strategy NOT NULL,
    merged_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id BIGINT REFERENCES actors(actor_id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id BIGINT,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_created
    ON audit_events(created_at DESC);

CREATE INDEX idx_audit_resource
    ON audit_events(resource_type, resource_id);

-- ============================================================
-- 10. AUDIT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION log_pr_state_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state IS DISTINCT FROM NEW.state THEN
        INSERT INTO audit_events (
            actor_id,
            action,
            resource_type,
            resource_id,
            details
        )
        VALUES (
            NULL,
            'PULL_REQUEST_STATE_CHANGED',
            'pull_request',
            NEW.pr_id,
            jsonb_build_object(
                'previous_state', OLD.state,
                'new_state', NEW.state
            )
        );
    END IF;

    NEW.updated_at = NOW();

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_pr_state_audit
BEFORE UPDATE ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION log_pr_state_change();

-- ============================================================
-- 11. REVIEWER ELIGIBILITY
-- ============================================================

CREATE OR REPLACE FUNCTION is_eligible_reviewer(
    p_pr_id BIGINT,
    p_reviewer_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_author BIGINT;
    v_repository BIGINT;
    v_role actor_role;
    v_active BOOLEAN;
    v_member BOOLEAN;
BEGIN
    SELECT author_id, repository_id
    INTO v_author, v_repository
    FROM pull_requests
    WHERE pr_id = p_pr_id;

    IF NOT FOUND OR p_reviewer_id = v_author THEN
        RETURN FALSE;
    END IF;

    SELECT role, active
    INTO v_role, v_active
    FROM actors
    WHERE actor_id = p_reviewer_id;

    IF NOT FOUND OR NOT v_active THEN
        RETURN FALSE;
    END IF;

    IF v_role NOT IN ('reviewer', 'maintainer', 'administrator') THEN
        RETURN FALSE;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM repository_members
        WHERE repository_id = v_repository
          AND actor_id = p_reviewer_id
    )
    INTO v_member;

    RETURN v_member;
END;
$$;

-- ============================================================
-- 12. MERGE ELIGIBILITY FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_merge_eligibility(
    p_pr_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reasons TEXT[],
    approval_count BIGINT,
    required_approval_count INTEGER
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_pr pull_requests%ROWTYPE;
    v_policy branch_protection_policies%ROWTYPE;
    v_policy_exists BOOLEAN;
    v_target_head VARCHAR(64);
    v_approval_count BIGINT;
    v_changes_requested BOOLEAN;
    v_missing_checks TEXT[];
    v_unresolved BIGINT;
    v_reasons TEXT[] := ARRAY[]::TEXT[];
BEGIN
    SELECT *
    INTO v_pr
    FROM pull_requests
    WHERE pr_id = p_pr_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Pull Request % does not exist', p_pr_id;
    END IF;

    SELECT head_commit_id
    INTO v_target_head
    FROM branches
    WHERE branch_id = v_pr.target_branch_id
      AND repository_id = v_pr.repository_id
      AND deleted_at IS NULL;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Target branch is unavailable';
    END IF;

    SELECT bp.*
    INTO v_policy
    FROM branch_protection_policies bp
    WHERE bp.branch_id = v_pr.target_branch_id;

    v_policy_exists := FOUND;

    IF NOT v_policy_exists THEN
        v_policy.required_approvals := 0;
        v_policy.require_resolved_conversations := FALSE;
        v_policy.require_up_to_date := FALSE;
        v_policy.enforce_stale_approval_dismissal := FALSE;
    END IF;

    IF v_pr.state <> 'open' THEN
        v_reasons := array_append(
            v_reasons,
            'Pull Request is not open'
        );
    END IF;

    IF v_pr.is_draft THEN
        v_reasons := array_append(
            v_reasons,
            'Draft must be published'
        );
    END IF;

    IF v_policy.require_up_to_date
       AND v_pr.base_commit_id <> v_target_head THEN
        v_reasons := array_append(
            v_reasons,
            'Target branch has advanced'
        );
    END IF;

    SELECT COUNT(DISTINCT reviewer_id)
    INTO v_approval_count
    FROM code_reviews
    WHERE pr_id = p_pr_id
      AND decision = 'approved'
      AND reviewed_commit_id = v_pr.head_commit_id
      AND is_eligible_reviewer(p_pr_id, reviewer_id);

    SELECT EXISTS (
        SELECT 1
        FROM code_reviews
        WHERE pr_id = p_pr_id
          AND decision = 'changes_requested'
          AND reviewed_commit_id = v_pr.head_commit_id
    )
    INTO v_changes_requested;

    IF v_changes_requested THEN
        v_reasons := array_append(
            v_reasons,
            'Changes have been requested'
        );
    END IF;

    IF v_approval_count < v_policy.required_approvals THEN
        v_reasons := array_append(
            v_reasons,
            'Insufficient eligible approvals'
        );
    END IF;

    IF v_policy_exists THEN
        SELECT ARRAY_AGG(rsc.check_name)
        INTO v_missing_checks
        FROM required_status_checks rsc
        WHERE rsc.policy_id = v_policy.policy_id
          AND NOT EXISTS (
              SELECT 1
              FROM status_checks sc
              WHERE sc.pr_id = p_pr_id
                AND sc.check_name = rsc.check_name
                AND sc.commit_id = v_pr.head_commit_id
                AND sc.status = 'success'
                AND sc.completed_at IS NOT NULL
          );

        IF COALESCE(array_length(v_missing_checks, 1), 0) > 0 THEN
            v_reasons := array_append(
                v_reasons,
                'Missing successful checks: '
                || array_to_string(v_missing_checks, ', ')
            );
        END IF;
    END IF;

    SELECT COUNT(*)
    INTO v_unresolved
    FROM review_comments
    WHERE pr_id = p_pr_id
      AND resolved = FALSE;

    IF v_policy.require_resolved_conversations
       AND v_unresolved > 0 THEN
        v_reasons := array_append(
            v_reasons,
            'Unresolved review conversations remain'
        );
    END IF;

    RETURN QUERY
    SELECT
        cardinality(v_reasons) = 0,
        v_reasons,
        v_approval_count,
        v_policy.required_approvals;
END;
$$;

-- ============================================================
-- 13. TRANSACTIONAL MERGE PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE merge_pull_request(
    p_pr_id BIGINT,
    p_actor_id BIGINT,
    p_strategy merge_strategy,
    p_merge_commit_id VARCHAR(64)
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_pr pull_requests%ROWTYPE;
    v_target branches%ROWTYPE;
    v_eligible BOOLEAN;
    v_reasons TEXT[];
    v_role actor_role;
BEGIN
    SELECT role
    INTO v_role
    FROM actors
    WHERE actor_id = p_actor_id
      AND active = TRUE;

    IF NOT FOUND OR v_role NOT IN ('maintainer', 'administrator') THEN
        RAISE EXCEPTION 'Actor is not authorized to merge';
    END IF;

    -- Lock the Pull Request and target branch to prevent
    -- concurrent merge decisions against stale state.
    SELECT *
    INTO v_pr
    FROM pull_requests
    WHERE pr_id = p_pr_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Pull Request not found';
    END IF;

    SELECT *
    INTO v_target
    FROM branches
    WHERE branch_id = v_pr.target_branch_id
    FOR UPDATE;

    SELECT e.eligible, e.reasons
    INTO v_eligible, v_reasons
    FROM evaluate_merge_eligibility(p_pr_id) e;

    IF NOT v_eligible THEN
        RAISE EXCEPTION 'Merge rejected: %',
            array_to_string(v_reasons, '; ');
    END IF;

    IF EXISTS (
        SELECT 1
        FROM commits
        WHERE commit_id = p_merge_commit_id
          AND repository_id = v_pr.repository_id
    ) THEN
        RAISE EXCEPTION 'Merge commit identifier already exists';
    END IF;

    INSERT INTO commits (
        commit_id,
        repository_id,
        author_id,
        message,
        parent_commit_id
    )
    VALUES (
        p_merge_commit_id,
        v_pr.repository_id,
        p_actor_id,
        'Merge Pull Request #' || p_pr_id,
        v_target.head_commit_id
    );

    UPDATE branches
    SET head_commit_id = p_merge_commit_id
    WHERE branch_id = v_pr.target_branch_id;

    UPDATE pull_requests
    SET state = 'merged',
        is_draft = FALSE,
        merged_at = NOW(),
        closed_at = NOW()
    WHERE pr_id = p_pr_id;

    INSERT INTO merge_history (
        pr_id,
        merged_by,
        merge_commit_id,
        strategy
    )
    VALUES (
        p_pr_id,
        p_actor_id,
        p_merge_commit_id,
        p_strategy
    );

    INSERT INTO audit_events (
        actor_id,
        action,
        resource_type,
        resource_id,
        details
    )
    VALUES (
        p_actor_id,
        'PULL_REQUEST_MERGED',
        'pull_request',
        p_pr_id,
        jsonb_build_object(
            'strategy', p_strategy,
            'merge_commit', p_merge_commit_id
        )
    );
END;
$$;

-- ============================================================
-- 14. REPORTING VIEWS
-- ============================================================

CREATE OR REPLACE VIEW dashboard_repository_metrics AS
SELECT
    r.repository_id,
    r.name,
    COUNT(DISTINCT b.branch_id) FILTER (
        WHERE b.deleted_at IS NULL
    ) AS active_branches,
    COUNT(DISTINCT c.commit_id) AS total_commits,
    COUNT(DISTINCT pr.pr_id) AS total_pull_requests,
    COUNT(DISTINCT pr.pr_id) FILTER (
        WHERE pr.state = 'open'
    ) AS open_pull_requests,
    COUNT(DISTINCT pr.pr_id) FILTER (
        WHERE pr.state = 'draft'
    ) AS draft_pull_requests,
    COUNT(DISTINCT pr.pr_id) FILTER (
        WHERE pr.state = 'merged'
    ) AS merged_pull_requests,
    COUNT(DISTINCT pr.pr_id) FILTER (
        WHERE pr.state = 'closed'
    ) AS closed_pull_requests
FROM repositories r
LEFT JOIN branches b
    ON b.repository_id = r.repository_id
LEFT JOIN commits c
    ON c.repository_id = r.repository_id
LEFT JOIN pull_requests pr
    ON pr.repository_id = r.repository_id
GROUP BY r.repository_id, r.name;

CREATE OR REPLACE VIEW dashboard_pr_overview AS
SELECT
    pr.pr_id,
    pr.title,
    repo.name AS repository,
    author.username AS author,
    source.name AS source_branch,
    target.name AS target_branch,
    pr.state,
    pr.is_draft,
    pr.created_at,
    pr.updated_at,
    COUNT(DISTINCT cr.review_id) FILTER (
        WHERE cr.decision = 'approved'
          AND cr.reviewed_commit_id = pr.head_commit_id
    ) AS current_approvals,
    COUNT(DISTINCT rc.comment_id) FILTER (
        WHERE rc.resolved = FALSE
    ) AS unresolved_comments,
    COUNT(DISTINCT sc.status_check_id) FILTER (
        WHERE sc.status = 'success'
          AND sc.commit_id = pr.head_commit_id
    ) AS successful_checks
FROM pull_requests pr
JOIN repositories repo
    ON repo.repository_id = pr.repository_id
JOIN actors author
    ON author.actor_id = pr.author_id
JOIN branches source
    ON source.branch_id = pr.source_branch_id
JOIN branches target
    ON target.branch_id = pr.target_branch_id
LEFT JOIN code_reviews cr
    ON cr.pr_id = pr.pr_id
LEFT JOIN review_comments rc
    ON rc.pr_id = pr.pr_id
LEFT JOIN status_checks sc
    ON sc.pr_id = pr.pr_id
GROUP BY
    pr.pr_id,
    repo.name,
    author.username,
    source.name,
    target.name;

-- ============================================================
-- 15. DASHBOARD ELIGIBILITY REPORT
-- ============================================================

CREATE OR REPLACE VIEW dashboard_merge_eligibility AS
SELECT
    pr.pr_id,
    pr.title,
    pr.repository_id,
    e.eligible,
    e.approval_count,
    e.required_approval_count,
    e.reasons
FROM pull_requests pr
CROSS JOIN LATERAL evaluate_merge_eligibility(pr.pr_id) e;

-- ============================================================
-- 16. SAMPLE DATA
-- ============================================================

INSERT INTO actors (
    username,
    email,
    role
)
VALUES
    ('platform-admin', 'admin@example.com', 'administrator'),
    ('developer-1', 'developer@example.com', 'developer'),
    ('reviewer-1', 'reviewer1@example.com', 'reviewer'),
    ('reviewer-2', 'reviewer2@example.com', 'reviewer'),
    ('release-manager', 'release@example.com', 'maintainer'),
    ('ci-service', 'ci@example.com', 'ci_system');

INSERT INTO repositories (
    name,
    owner_id,
    visibility,
    default_branch
)
SELECT
    'enterprise-admin-platform',
    actor_id,
    'private',
    'main'
FROM actors
WHERE username = 'platform-admin';

INSERT INTO repository_members (
    repository_id,
    actor_id,
    member_role
)
SELECT
    r.repository_id,
    a.actor_id,
    CASE a.username
        WHEN 'platform-admin' THEN 'admin'
        WHEN 'release-manager' THEN 'maintain'
        WHEN 'developer-1' THEN 'write'
        ELSE 'write'
    END
FROM repositories r
CROSS JOIN actors a
WHERE a.username IN (
    'platform-admin',
    'developer-1',
    'reviewer-1',
    'reviewer-2',
    'release-manager',
    'ci-service'
);

INSERT INTO commits (
    commit_id,
    repository_id,
    author_id,
    message
)
SELECT
    'a10000000001',
    r.repository_id,
    a.actor_id,
    'Initial production release'
FROM repositories r
CROSS JOIN actors a
WHERE a.username = 'platform-admin';

INSERT INTO commits (
    commit_id,
    repository_id,
    author_id,
    message,
    parent_commit_id
)
SELECT
    'b20000000002',
    r.repository_id,
    a.actor_id,
    'Implement repository analytics dashboard',
    'a10000000001'
FROM repositories r
CROSS JOIN actors a
WHERE a.username = 'developer-1';

INSERT INTO commits (
    commit_id,
    repository_id,
    author_id,
    message,
    parent_commit_id
)
SELECT
    'c30000000003',
    r.repository_id,
    a.actor_id,
    'Update security dependencies',
    'a10000000001'
FROM repositories r
CROSS JOIN actors a
WHERE a.username = 'developer-1';

INSERT INTO branches (
    repository_id,
    name,
    head_commit_id,
    protected
)
SELECT
    repository_id,
    'main',
    'a10000000001',
    TRUE
FROM repositories;

INSERT INTO branches (
    repository_id,
    name,
    head_commit_id,
    protected
)
SELECT
    repository_id,
    'feature/analytics',
    'b20000000002',
    FALSE
FROM repositories;

INSERT INTO branches (
    repository_id,
    name,
    head_commit_id,
    protected
)
SELECT
    repository_id,
    'security/dependencies',
    'c30000000003',
    FALSE
FROM repositories;

INSERT INTO branch_protection_policies (
    branch_id,
    required_approvals,
    require_resolved_conversations,
    require_up_to_date,
    require_linear_history,
    allow_direct_push,
    allow_force_push,
    allow_branch_deletion,
    allow_admin_bypass
)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    FALSE
FROM branches
WHERE name = 'main';

INSERT INTO required_status_checks (
    policy_id,
    check_name
)
SELECT
    policy_id,
    required_name
FROM branch_protection_policies
CROSS JOIN (
    VALUES ('build'), ('tests'), ('security')
) AS required(required_name);

INSERT INTO pull_requests (
    repository_id,
    author_id,
    source_branch_id,
    target_branch_id,
    title,
    state,
    base_commit_id,
    head_commit_id
)
SELECT
    r.repository_id,
    developer.actor_id,
    source.branch_id,
    target.branch_id,
    'Implement analytics dashboard',
    'open',
    'a10000000001',
    'b20000000002'
FROM repositories r
JOIN actors developer
    ON developer.username = 'developer-1'
JOIN branches source
    ON source.repository_id = r.repository_id
   AND source.name = 'feature/analytics'
JOIN branches target
    ON target.repository_id = r.repository_id
   AND target.name = 'main';

INSERT INTO pull_requests (
    repository_id,
    author_id,
    source_branch_id,
    target_branch_id,
    title,
    state,
    base_commit_id,
    head_commit_id
)
SELECT
    r.repository_id,
    developer.actor_id,
    source.branch_id,
    target.branch_id,
    'Update security dependencies',
    'open',
    'a10000000001',
    'c30000000003'
FROM repositories r
JOIN actors developer
    ON developer.username = 'developer-1'
JOIN branches source
    ON source.repository_id = r.repository_id
   AND source.name = 'security/dependencies'
JOIN branches target
    ON target.repository_id = r.repository_id
   AND target.name = 'main';

INSERT INTO code_reviews (
    pr_id,
    reviewer_id,
    decision,
    reviewed_commit_id,
    review_comment
)
SELECT
    pr.pr_id,
    reviewer.actor_id,
    'approved',
    pr.head_commit_id,
    'Implementation and test coverage verified.'
FROM pull_requests pr
CROSS JOIN actors reviewer
WHERE pr.title = 'Implement analytics dashboard'
  AND reviewer.username IN ('reviewer-1', 'reviewer-2');

INSERT INTO status_checks (
    pr_id,
    check_name,
    status,
    commit_id,
    completed_at
)
SELECT
    pr.pr_id,
    checks.name,
    'success',
    pr.head_commit_id,
    NOW()
FROM pull_requests pr
CROSS JOIN (
    VALUES ('build'), ('tests'), ('security')
) AS checks(name)
WHERE pr.title = 'Implement analytics dashboard';

INSERT INTO status_checks (
    pr_id,
    check_name,
    status,
    commit_id
)
SELECT
    pr.pr_id,
    'build',
    'failure',
    pr.head_commit_id
FROM pull_requests pr
WHERE pr.title = 'Update security dependencies';

-- ============================================================
-- 17. RETRIEVAL QUERIES
-- ============================================================

-- All repositories with operational metrics.
SELECT *
FROM dashboard_repository_metrics
ORDER BY name;

-- Current Pull Request overview.
SELECT *
FROM dashboard_pr_overview
ORDER BY updated_at DESC;

-- Review decisions.
SELECT
    pr.pr_id,
    pr.title,
    a.username AS reviewer,
    cr.decision,
    cr.reviewed_commit_id,
    cr.submitted_at
FROM code_reviews cr
JOIN pull_requests pr
    ON pr.pr_id = cr.pr_id
JOIN actors a
    ON a.actor_id = cr.reviewer_id
ORDER BY cr.submitted_at DESC;

-- ============================================================
-- 18. ELIGIBILITY AND VALIDATION REPORTS
-- ============================================================

SELECT *
FROM dashboard_merge_eligibility
ORDER BY pr_id;

-- Find open Pull Requests with incomplete CI checks.
SELECT
    pr.pr_id,
    pr.title,
    sc.check_name,
    sc.status
FROM pull_requests pr
JOIN status_checks sc
    ON sc.pr_id = pr.pr_id
WHERE pr.state = 'open'
  AND sc.status <> 'success';

-- Find unresolved review conversations.
SELECT
    pr.pr_id,
    pr.title,
    COUNT(rc.comment_id) AS unresolved_comments
FROM pull_requests pr
JOIN review_comments rc
    ON rc.pr_id = pr.pr_id
WHERE rc.resolved = FALSE
GROUP BY pr.pr_id, pr.title;

-- Approval aggregation.
SELECT
    pr.pr_id,
    pr.title,
    COUNT(DISTINCT cr.reviewer_id) FILTER (
        WHERE cr.decision = 'approved'
          AND cr.reviewed_commit_id = pr.head_commit_id
    ) AS current_approvals
FROM pull_requests pr
LEFT JOIN code_reviews cr
    ON cr.pr_id = pr.pr_id
GROUP BY pr.pr_id, pr.title;

-- ============================================================
-- 19. TRANSACTION EXAMPLE
-- ============================================================

-- Demonstrates a rejected merge without persisting partial changes.
-- The SAVEPOINT allows the reporting transaction to continue.

SAVEPOINT before_merge_attempt;

DO $$
DECLARE
    v_pr BIGINT;
    v_eligible BOOLEAN;
    v_reasons TEXT[];
BEGIN
    SELECT pr_id
    INTO v_pr
    FROM pull_requests
    WHERE title = 'Implement analytics dashboard';

    SELECT eligible, reasons
    INTO v_eligible, v_reasons
    FROM evaluate_merge_eligibility(v_pr);

    RAISE NOTICE 'PR % eligibility: %', v_pr, v_eligible;
    RAISE NOTICE 'Evaluation reasons: %', v_reasons;

    IF NOT v_eligible THEN
        RAISE NOTICE 'Merge cannot proceed.';
    END IF;
END;
$$;

-- ============================================================
-- 20. ADMIN DASHBOARD AGGREGATION
-- ============================================================

SELECT
    COUNT(*) AS total_pull_requests,
    COUNT(*) FILTER (
        WHERE state = 'open'
    ) AS open_pull_requests,
    COUNT(*) FILTER (
        WHERE state = 'draft'
    ) AS draft_pull_requests,
    COUNT(*) FILTER (
        WHERE state = 'merged'
    ) AS merged_pull_requests,
    COUNT(*) FILTER (
        WHERE state = 'closed'
    ) AS closed_pull_requests
FROM pull_requests;

-- Current merge-eligible Pull Requests.
SELECT
    pr_id,
    title,
    approval_count,
    required_approval_count
FROM dashboard_merge_eligibility
WHERE eligible = TRUE;

-- Recent audit activity.
SELECT
    ae.event_id,
    a.username,
    ae.action,
    ae.resource_type,
    ae.resource_id,
    ae.details,
    ae.created_at
FROM audit_events ae
LEFT JOIN actors a
    ON a.actor_id = ae.actor_id
ORDER BY ae.created_at DESC
LIMIT 50;

RELEASE SAVEPOINT before_merge_attempt;

COMMIT;

-- ============================================================
-- PRODUCTION IMPLEMENTATION NOTES
--
-- 1. Authentication and authorization should be enforced by
--    the application and database permissions.
--
-- 2. Database transactions should wrap eligibility evaluation,
--    branch locking, commit creation and merge-history writes.
--
-- 3. Git ancestry and actual merge-conflict detection require
--    integration with the underlying Git implementation.
--
-- 4. A production review policy should also consider dismissed
--    reviews, approval freshness, team membership and
--    repository-specific reviewer eligibility.
--
-- 5. Audit records should be append-only for application roles.
--
-- 6. Additional partial indexes should be based on observed
--    query plans and production workload.
-- ============================================================
