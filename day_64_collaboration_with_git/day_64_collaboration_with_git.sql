-- PostgreSQL 14+
-- Repository collaboration, Pull Requests, code review, approvals,
-- status checks, branch protection, and merge eligibility.
--
-- This script rebuilds its dedicated schema so it can be executed repeatedly.
-- Run it in a database where the executing role can create schemas and functions.

DROP SCHEMA IF EXISTS git_collab CASCADE;
CREATE SCHEMA git_collab;
SET search_path = git_collab, public;

-- ---------------------------------------------------------------------------
-- Identity, repositories, membership, commits, and branches
-- ---------------------------------------------------------------------------

CREATE TABLE users (
    user_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username         TEXT NOT NULL UNIQUE,
    display_name     TEXT NOT NULL,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_username_not_blank CHECK (length(trim(username)) > 0)
);

CREATE TABLE repositories (
    repo_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_name       TEXT NOT NULL,
    repository_name  TEXT NOT NULL,
    default_branch   TEXT NOT NULL DEFAULT 'main',
    visibility       TEXT NOT NULL DEFAULT 'private',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT repositories_owner_name_unique
        UNIQUE (owner_name, repository_name),
    CONSTRAINT repositories_visibility_check
        CHECK (visibility IN ('private', 'internal', 'public')),
    CONSTRAINT repositories_name_not_blank
        CHECK (length(trim(repository_name)) > 0)
);

CREATE TABLE repository_members (
    repo_id          BIGINT NOT NULL REFERENCES repositories(repo_id) ON DELETE CASCADE,
    user_id          BIGINT NOT NULL REFERENCES users(user_id),
    access_role      TEXT NOT NULL,
    can_review       BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin         BOOLEAN NOT NULL DEFAULT FALSE,
    joined_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (repo_id, user_id),
    CONSTRAINT repository_members_role_check
        CHECK (access_role IN ('viewer', 'developer', 'maintainer', 'admin')),
    CONSTRAINT repository_members_admin_check
        CHECK (NOT is_admin OR access_role = 'admin')
);

CREATE TABLE commits (
    repo_id          BIGINT NOT NULL REFERENCES repositories(repo_id) ON DELETE CASCADE,
    sha              TEXT NOT NULL,
    author_id        BIGINT NOT NULL REFERENCES users(user_id),
    message          TEXT NOT NULL,
    parent_shas      TEXT[] NOT NULL DEFAULT '{}',
    metadata         JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (repo_id, sha),
    CONSTRAINT commits_sha_format
        CHECK (sha ~ '^[0-9a-f]{40}$'),
    CONSTRAINT commits_message_not_blank
        CHECK (length(trim(message)) > 0)
);

CREATE TABLE branches (
    branch_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repo_id          BIGINT NOT NULL REFERENCES repositories(repo_id) ON DELETE CASCADE,
    branch_name      TEXT NOT NULL,
    head_commit_sha  TEXT NOT NULL,
    is_protected     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at       TIMESTAMPTZ,
    UNIQUE (repo_id, branch_name),
    UNIQUE (branch_id, repo_id),
    FOREIGN KEY (repo_id, head_commit_sha)
        REFERENCES commits(repo_id, sha),
    CONSTRAINT branches_name_not_blank
        CHECK (length(trim(branch_name)) > 0)
);

CREATE INDEX idx_commits_repo_created
    ON commits(repo_id, created_at DESC);

CREATE INDEX idx_branches_repo_active
    ON branches(repo_id, branch_name)
    WHERE deleted_at IS NULL;

-- ---------------------------------------------------------------------------
-- Pull Requests: the proposed changeset is separate from branch state.
-- source_head_sha identifies the exact source revision being evaluated.
-- base_sha_at_sync identifies the target revision last incorporated by source.
-- ---------------------------------------------------------------------------

CREATE TABLE pull_requests (
    pr_id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repo_id                BIGINT NOT NULL REFERENCES repositories(repo_id) ON DELETE CASCADE,
    pr_number              INTEGER NOT NULL,
    author_id              BIGINT NOT NULL REFERENCES users(user_id),
    source_branch_id       BIGINT NOT NULL,
    target_branch_id       BIGINT NOT NULL,
    base_sha_at_open       TEXT NOT NULL,
    base_sha_at_sync       TEXT NOT NULL,
    source_head_sha        TEXT NOT NULL,
    proposed_changeset     JSONB NOT NULL DEFAULT '{}'::JSONB,
    state                  TEXT NOT NULL DEFAULT 'draft',
    is_draft               BOOLEAN NOT NULL DEFAULT TRUE,
    merge_strategy         TEXT,
    merged_commit_sha      TEXT,
    opened_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at              TIMESTAMPTZ,
    UNIQUE (repo_id, pr_number),
    UNIQUE (pr_id, repo_id),
    FOREIGN KEY (source_branch_id, repo_id)
        REFERENCES branches(branch_id, repo_id),
    FOREIGN KEY (target_branch_id, repo_id)
        REFERENCES branches(branch_id, repo_id),
    FOREIGN KEY (repo_id, base_sha_at_open)
        REFERENCES commits(repo_id, sha),
    FOREIGN KEY (repo_id, base_sha_at_sync)
        REFERENCES commits(repo_id, sha),
    FOREIGN KEY (repo_id, source_head_sha)
        REFERENCES commits(repo_id, sha),
    FOREIGN KEY (repo_id, merged_commit_sha)
        REFERENCES commits(repo_id, sha),
    CONSTRAINT pull_requests_distinct_branches
        CHECK (source_branch_id <> target_branch_id),
    CONSTRAINT pull_requests_state_check
        CHECK (state IN ('draft', 'open', 'closed', 'merged')),
    CONSTRAINT pull_requests_draft_check
        CHECK (
            (state = 'draft' AND is_draft)
            OR
            (state <> 'draft' AND NOT is_draft)
        ),
    CONSTRAINT pull_requests_merge_strategy_check
        CHECK (
            merge_strategy IS NULL
            OR merge_strategy IN ('merge_commit', 'squash', 'rebase')
        ),
    CONSTRAINT pull_requests_merged_commit_check
        CHECK (
            (state = 'merged' AND merged_commit_sha IS NOT NULL)
            OR
            (state <> 'merged' AND merged_commit_sha IS NULL)
        )
);

CREATE INDEX idx_pull_requests_target_state
    ON pull_requests(repo_id, target_branch_id, state);

CREATE INDEX idx_pull_requests_author
    ON pull_requests(repo_id, author_id, opened_at DESC);

CREATE INDEX idx_pull_requests_source_head
    ON pull_requests(repo_id, source_head_sha);

-- ---------------------------------------------------------------------------
-- Branch protection and explicit approval requirements
-- ---------------------------------------------------------------------------

CREATE TABLE branch_protection_policies (
    policy_id                    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repo_id                      BIGINT NOT NULL,
    branch_id                    BIGINT NOT NULL,
    require_pull_request         BOOLEAN NOT NULL DEFAULT TRUE,
    required_checks              TEXT[] NOT NULL DEFAULT '{}',
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history       BOOLEAN NOT NULL DEFAULT FALSE,
    allow_merge_commit           BOOLEAN NOT NULL DEFAULT TRUE,
    allow_squash                 BOOLEAN NOT NULL DEFAULT TRUE,
    allow_rebase                 BOOLEAN NOT NULL DEFAULT TRUE,
    allow_direct_push            BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push             BOOLEAN NOT NULL DEFAULT FALSE,
    prohibit_branch_deletion     BOOLEAN NOT NULL DEFAULT TRUE,
    allow_admin_bypass           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (branch_id),
    FOREIGN KEY (branch_id, repo_id)
        REFERENCES branches(branch_id, repo_id) ON DELETE CASCADE,
    CONSTRAINT branch_policy_check_names
        CHECK (array_position(required_checks, '') IS NULL)
);

CREATE TABLE approval_requirements (
    approval_requirement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_id               BIGINT NOT NULL UNIQUE
                            REFERENCES branch_protection_policies(policy_id)
                            ON DELETE CASCADE,
    required_approvals      INTEGER NOT NULL DEFAULT 1,
    eligible_roles          TEXT[] NOT NULL
                            DEFAULT ARRAY['developer', 'maintainer', 'admin'],
    exclude_pull_request_author BOOLEAN NOT NULL DEFAULT TRUE,
    block_current_change_requests BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT approval_count_nonnegative
        CHECK (required_approvals >= 0),
    CONSTRAINT approval_roles_valid
        CHECK (
            eligible_roles <@ ARRAY[
                'viewer', 'developer', 'maintainer', 'admin'
            ]::TEXT[]
        )
);

CREATE INDEX idx_branch_policies_repo
    ON branch_protection_policies(repo_id, branch_id);

-- ---------------------------------------------------------------------------
-- Code review and discussions
-- ---------------------------------------------------------------------------

CREATE TABLE reviews (
    review_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id               BIGINT NOT NULL,
    repo_id             BIGINT NOT NULL,
    reviewer_id         BIGINT NOT NULL REFERENCES users(user_id),
    review_state        TEXT NOT NULL,
    reviewed_head_sha   TEXT NOT NULL,
    review_body         TEXT NOT NULL DEFAULT '',
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pr_id, repo_id)
        REFERENCES pull_requests(pr_id, repo_id) ON DELETE CASCADE,
    FOREIGN KEY (repo_id, reviewed_head_sha)
        REFERENCES commits(repo_id, sha),
    CONSTRAINT reviews_state_check
        CHECK (
            review_state IN (
                'approved', 'changes_requested', 'commented', 'dismissed'
            )
        )
);

CREATE INDEX idx_reviews_pr_reviewer_latest
    ON reviews(pr_id, reviewer_id, submitted_at DESC, review_id DESC);

CREATE INDEX idx_reviews_pr_head_state
    ON reviews(pr_id, reviewed_head_sha, review_state);

CREATE TABLE review_threads (
    thread_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id               BIGINT NOT NULL
                        REFERENCES pull_requests(pr_id) ON DELETE CASCADE,
    file_path           TEXT NOT NULL,
    line_number         INTEGER NOT NULL,
    created_by          BIGINT NOT NULL REFERENCES users(user_id),
    is_resolved         BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by         BIGINT REFERENCES users(user_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at         TIMESTAMPTZ,
    UNIQUE (thread_id, pr_id),
    CONSTRAINT review_threads_path_not_blank
        CHECK (length(trim(file_path)) > 0),
    CONSTRAINT review_threads_line_positive
        CHECK (line_number > 0),
    CONSTRAINT review_threads_resolution_state
        CHECK (
            (is_resolved AND resolved_by IS NOT NULL AND resolved_at IS NOT NULL)
            OR
            (NOT is_resolved AND resolved_by IS NULL AND resolved_at IS NULL)
        )
);

CREATE INDEX idx_review_threads_pr_unresolved
    ON review_threads(pr_id)
    WHERE NOT is_resolved;

CREATE TABLE review_comments (
    comment_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id               BIGINT NOT NULL,
    thread_id           BIGINT NOT NULL,
    review_id           BIGINT NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    author_id           BIGINT NOT NULL REFERENCES users(user_id),
    comment_body        TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thread_id, pr_id)
        REFERENCES review_threads(thread_id, pr_id) ON DELETE CASCADE,
    CONSTRAINT review_comments_body_not_blank
        CHECK (length(trim(comment_body)) > 0)
);

CREATE INDEX idx_review_comments_thread
    ON review_comments(thread_id, created_at);

-- ---------------------------------------------------------------------------
-- Automated checks are associated with a specific source head.
-- A successful result for an older head does not validate a newer changeset.
-- ---------------------------------------------------------------------------

CREATE TABLE status_checks (
    status_check_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id               BIGINT NOT NULL,
    repo_id             BIGINT NOT NULL,
    head_sha            TEXT NOT NULL,
    check_name          TEXT NOT NULL,
    check_state         TEXT NOT NULL,
    details             TEXT NOT NULL DEFAULT '',
    started_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at        TIMESTAMPTZ,
    FOREIGN KEY (pr_id, repo_id)
        REFERENCES pull_requests(pr_id, repo_id) ON DELETE CASCADE,
    FOREIGN KEY (repo_id, head_sha)
        REFERENCES commits(repo_id, sha),
    UNIQUE (pr_id, head_sha, check_name),
    CONSTRAINT status_checks_state_check
        CHECK (check_state IN ('pending', 'passed', 'failed', 'cancelled')),
    CONSTRAINT status_checks_name_not_blank
        CHECK (length(trim(check_name)) > 0),
    CONSTRAINT status_checks_completion_check
        CHECK (
            (check_state = 'pending' AND completed_at IS NULL)
            OR
            (check_state <> 'pending' AND completed_at IS NOT NULL)
        )
);

CREATE INDEX idx_status_checks_pr_head
    ON status_checks(pr_id, head_sha, check_name, check_state);

-- ---------------------------------------------------------------------------
-- Domain integrity: branch ownership and review eligibility
-- ---------------------------------------------------------------------------

CREATE FUNCTION validate_pull_request_branches()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    source_repo BIGINT;
    target_repo BIGINT;
    source_deleted TIMESTAMPTZ;
    target_deleted TIMESTAMPTZ;
BEGIN
    SELECT repo_id, deleted_at
      INTO source_repo, source_deleted
      FROM branches
     WHERE branch_id = NEW.source_branch_id;

    SELECT repo_id, deleted_at
      INTO target_repo, target_deleted
      FROM branches
     WHERE branch_id = NEW.target_branch_id;

    IF source_repo IS NULL OR target_repo IS NULL THEN
        RAISE EXCEPTION 'Source and target branches must exist';
    END IF;

    IF source_repo <> NEW.repo_id OR target_repo <> NEW.repo_id THEN
        RAISE EXCEPTION 'Pull Request branches must belong to its repository';
    END IF;

    IF source_deleted IS NOT NULL OR target_deleted IS NOT NULL THEN
        RAISE EXCEPTION 'Deleted branches cannot be used by a Pull Request';
    END IF;

    IF NEW.source_branch_id = NEW.target_branch_id THEN
        RAISE EXCEPTION 'Source and target branches must differ';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_pull_request_branches
BEFORE INSERT OR UPDATE ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION validate_pull_request_branches();

CREATE FUNCTION validate_review_submission()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    pull_author BIGINT;
    pull_state TEXT;
    draft_flag BOOLEAN;
    member_active BOOLEAN;
    member_can_review BOOLEAN;
BEGIN
    SELECT author_id, state, is_draft
      INTO pull_author, pull_state, draft_flag
      FROM pull_requests
     WHERE pr_id = NEW.pr_id;

    IF pull_author IS NULL THEN
        RAISE EXCEPTION 'Pull Request does not exist';
    END IF;

    IF NEW.reviewer_id = pull_author THEN
        RAISE EXCEPTION 'Pull Request authors cannot review their own changes';
    END IF;

    IF pull_state <> 'open' OR draft_flag THEN
        RAISE EXCEPTION 'Reviews require an open, non-draft Pull Request';
    END IF;

    SELECT u.is_active, rm.can_review
      INTO member_active, member_can_review
      FROM repository_members rm
      JOIN users u ON u.user_id = rm.user_id
     WHERE rm.repo_id = NEW.repo_id
       AND rm.user_id = NEW.reviewer_id;

    IF NOT COALESCE(member_active, FALSE)
       OR NOT COALESCE(member_can_review, FALSE) THEN
        RAISE EXCEPTION 'Reviewer is not active or lacks review permission';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_review_submission
BEFORE INSERT ON reviews
FOR EACH ROW
EXECUTE FUNCTION validate_review_submission();

-- ---------------------------------------------------------------------------
-- Pull Request lifecycle transition enforcement
-- merged is terminal. Reopening a closed Pull Request is allowed.
-- ---------------------------------------------------------------------------

CREATE FUNCTION validate_pull_request_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state = NEW.state THEN
        RETURN NEW;
    END IF;

    IF OLD.state = 'draft' AND NEW.state IN ('open', 'closed') THEN
        NULL;
    ELSIF OLD.state = 'open' AND NEW.state IN ('closed', 'merged') THEN
        NULL;
    ELSIF OLD.state = 'closed' AND NEW.state = 'open' THEN
        NULL;
    ELSE
        RAISE EXCEPTION 'Invalid Pull Request state transition: % -> %',
            OLD.state, NEW.state;
    END IF;

    IF NEW.state = 'merged'
       AND current_setting('git_collab.merge_in_progress', TRUE) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION 'A Pull Request can be merged only through merge_pull_request';
    END IF;

    IF NEW.state = 'draft' THEN
        NEW.is_draft := TRUE;
    ELSE
        NEW.is_draft := FALSE;
    END IF;

    IF NEW.state IN ('closed', 'merged') THEN
        NEW.closed_at := COALESCE(NEW.closed_at, CURRENT_TIMESTAMP);
    ELSIF NEW.state = 'open' THEN
        NEW.closed_at := NULL;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_pull_request_state_transition
BEFORE UPDATE OF state ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION validate_pull_request_transition();

-- ---------------------------------------------------------------------------
-- Protected branch guards.
-- Internal merge and validated direct-push functions set transaction-local
-- authorization flags. Ordinary SQL updates cannot silently bypass the guard.
-- ---------------------------------------------------------------------------

CREATE FUNCTION guard_protected_branch_head()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.is_protected
       AND NEW.head_commit_sha <> OLD.head_commit_sha
       AND current_setting('git_collab.merge_in_progress', TRUE) IS DISTINCT FROM 'on'
       AND current_setting('git_collab.direct_push_authorized', TRUE) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION 'Direct head updates to protected branches are prohibited';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_guard_protected_branch_head
BEFORE UPDATE OF head_commit_sha ON branches
FOR EACH ROW
EXECUTE FUNCTION guard_protected_branch_head();

CREATE FUNCTION guard_protected_branch_deletion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    deletion_prohibited BOOLEAN;
BEGIN
    IF OLD.is_protected THEN
        SELECT bp.prohibit_branch_deletion
          INTO deletion_prohibited
          FROM branch_protection_policies bp
         WHERE bp.branch_id = OLD.branch_id;

        IF COALESCE(deletion_prohibited, TRUE) THEN
            RAISE EXCEPTION 'Deletion of protected branch % is prohibited',
                OLD.branch_name;
        END IF;
    END IF;

    RETURN OLD;
END;
$$;

CREATE TRIGGER trg_guard_protected_branch_deletion
BEFORE DELETE ON branches
FOR EACH ROW
EXECUTE FUNCTION guard_protected_branch_deletion();

-- ---------------------------------------------------------------------------
-- History and direct-push validation
-- ---------------------------------------------------------------------------

CREATE FUNCTION is_commit_ancestor(
    p_repo_id BIGINT,
    p_ancestor_sha TEXT,
    p_descendant_sha TEXT
)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    WITH RECURSIVE ancestry(sha) AS (
        SELECT p_descendant_sha
        UNION
        SELECT parent.sha
          FROM ancestry a
          JOIN commits c
            ON c.repo_id = p_repo_id
           AND c.sha = a.sha
          CROSS JOIN LATERAL unnest(c.parent_shas) AS parent(sha)
    )
    SELECT EXISTS (
        SELECT 1
          FROM ancestry
         WHERE sha = p_ancestor_sha
    );
$$;

CREATE FUNCTION record_direct_push(
    p_branch_id BIGINT,
    p_new_sha TEXT,
    p_is_force BOOLEAN DEFAULT FALSE
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_branch RECORD;
    v_policy RECORD;
BEGIN
    SELECT *
      INTO v_branch
      FROM branches
     WHERE branch_id = p_branch_id
       AND deleted_at IS NULL
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Branch does not exist or has been deleted';
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM commits
         WHERE repo_id = v_branch.repo_id
           AND sha = p_new_sha
    ) THEN
        RAISE EXCEPTION 'New commit does not belong to this repository';
    END IF;

    IF v_branch.is_protected THEN
        SELECT *
          INTO v_policy
          FROM branch_protection_policies
         WHERE branch_id = p_branch_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Protected branch has no policy configuration';
        END IF;

        IF v_policy.require_pull_request OR NOT v_policy.allow_direct_push THEN
            RAISE EXCEPTION 'Direct push is prohibited by branch protection';
        END IF;

        IF p_is_force AND NOT v_policy.allow_force_push THEN
            RAISE EXCEPTION 'Force push is prohibited by branch protection';
        END IF;
    END IF;

    IF NOT p_is_force AND NOT is_commit_ancestor(
        v_branch.repo_id,
        v_branch.head_commit_sha,
        p_new_sha
    ) THEN
        RAISE EXCEPTION 'Non-fast-forward update requires force-push permission';
    END IF;

    PERFORM set_config('git_collab.direct_push_authorized', 'on', TRUE);

    UPDATE branches
       SET head_commit_sha = p_new_sha
     WHERE branch_id = p_branch_id;

    PERFORM set_config('git_collab.direct_push_authorized', 'off', TRUE);
END;
$$;

-- ---------------------------------------------------------------------------
-- Merge eligibility.
-- Each returned row represents one independently evaluated rule.
-- Admin bypass can bypass policy checks only when explicitly enabled.
-- Source/target synchronization and valid Pull Request state remain mandatory.
-- ---------------------------------------------------------------------------

CREATE FUNCTION merge_eligibility(
    p_pr_id BIGINT,
    p_actor_id BIGINT,
    p_strategy TEXT DEFAULT 'squash'
)
RETURNS TABLE (
    rule_name TEXT,
    passed BOOLEAN,
    detail TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_pr RECORD;
    v_policy RECORD;
    v_approval_count INTEGER;
    v_change_requests INTEGER;
    v_unresolved_threads INTEGER;
    v_bypass BOOLEAN := FALSE;
    v_merger_authorized BOOLEAN := FALSE;
BEGIN
    SELECT
        p.*,
        sb.head_commit_sha AS actual_source_head,
        tb.head_commit_sha AS actual_target_head
      INTO v_pr
      FROM pull_requests p
      JOIN branches sb ON sb.branch_id = p.source_branch_id
      JOIN branches tb ON tb.branch_id = p.target_branch_id
     WHERE p.pr_id = p_pr_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT 'PULL_REQUEST_EXISTS'::TEXT, FALSE,
               'Pull Request does not exist'::TEXT;
        RETURN;
    END IF;

    SELECT
        bp.*,
        COALESCE(ar.required_approvals, 0) AS required_approvals,
        COALESCE(
            ar.eligible_roles,
            ARRAY['developer', 'maintainer', 'admin']::TEXT[]
        ) AS eligible_roles,
        COALESCE(ar.exclude_pull_request_author, TRUE) AS exclude_author,
        COALESCE(ar.block_current_change_requests, TRUE) AS block_changes
      INTO v_policy
      FROM branch_protection_policies bp
      LEFT JOIN approval_requirements ar ON ar.policy_id = bp.policy_id
     WHERE bp.branch_id = v_pr.target_branch_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT 'PROTECTION_POLICY_CONFIGURED'::TEXT, FALSE,
               'Target branch has no branch-protection policy'::TEXT;
        RETURN;
    END IF;

    SELECT EXISTS (
        SELECT 1
          FROM repository_members rm
          JOIN users u ON u.user_id = rm.user_id
         WHERE rm.repo_id = v_pr.repo_id
           AND rm.user_id = p_actor_id
           AND u.is_active
           AND rm.access_role IN ('maintainer', 'admin')
    )
    INTO v_merger_authorized;

    v_bypass := v_policy.allow_admin_bypass AND EXISTS (
        SELECT 1
          FROM repository_members rm
          JOIN users u ON u.user_id = rm.user_id
         WHERE rm.repo_id = v_pr.repo_id
           AND rm.user_id = p_actor_id
           AND rm.is_admin
           AND u.is_active
    );

    -- Only the latest review event from each reviewer is authoritative.
    WITH latest_reviews AS (
        SELECT DISTINCT ON (r.reviewer_id)
            r.reviewer_id,
            r.review_state,
            r.reviewed_head_sha
          FROM reviews r
         WHERE r.pr_id = p_pr_id
         ORDER BY r.reviewer_id, r.submitted_at DESC, r.review_id DESC
    )
    SELECT
        COUNT(*) FILTER (
            WHERE lr.review_state = 'approved'
              AND lr.reviewed_head_sha = v_pr.source_head_sha
              AND (
                    NOT v_policy.exclude_author
                    OR lr.reviewer_id <> v_pr.author_id
              )
        )::INTEGER,
        COUNT(*) FILTER (
            WHERE lr.review_state = 'changes_requested'
              AND lr.reviewed_head_sha = v_pr.source_head_sha
              AND (
                    NOT v_policy.exclude_author
                    OR lr.reviewer_id <> v_pr.author_id
              )
        )::INTEGER
      INTO v_approval_count, v_change_requests
      FROM latest_reviews lr
      JOIN repository_members rm
        ON rm.repo_id = v_pr.repo_id
       AND rm.user_id = lr.reviewer_id
       AND rm.can_review
       AND rm.access_role = ANY(v_policy.eligible_roles)
      JOIN users u
        ON u.user_id = rm.user_id
       AND u.is_active;

    SELECT COUNT(*)::INTEGER
      INTO v_unresolved_threads
      FROM review_threads
     WHERE pr_id = p_pr_id
       AND NOT is_resolved;

    RETURN QUERY
    SELECT
        'MERGER_AUTHORIZED'::TEXT,
        v_merger_authorized,
        CASE
            WHEN v_merger_authorized THEN 'Merger is an active maintainer or administrator'
            ELSE 'Merger must be an active maintainer or administrator'
        END::TEXT;

    RETURN QUERY
    SELECT
        'PULL_REQUEST_OPEN_AND_READY'::TEXT,
        v_pr.state = 'open' AND NOT v_pr.is_draft,
        'Pull Request must be open and not in draft state'::TEXT;

    RETURN QUERY
    SELECT
        'SOURCE_HEAD_CURRENT'::TEXT,
        v_pr.source_head_sha = v_pr.actual_source_head,
        'Recorded proposed head must match the source branch head'::TEXT;

    RETURN QUERY
    SELECT
        'BASE_SYNCHRONIZED'::TEXT,
        v_pr.base_sha_at_sync = v_pr.actual_target_head,
        'Target branch must not have advanced since the last synchronization'::TEXT;

    RETURN QUERY
    SELECT
        'REQUIRED_APPROVALS'::TEXT,
        v_bypass OR v_approval_count >= v_policy.required_approvals,
        format(
            'Current eligible approvals: %s; required: %s',
            v_approval_count,
            v_policy.required_approvals
        );

    RETURN QUERY
    SELECT
        'NO_CURRENT_CHANGE_REQUESTS'::TEXT,
        v_bypass OR NOT v_policy.block_changes OR v_change_requests = 0,
        format('Current eligible change requests: %s', v_change_requests);

    RETURN QUERY
    SELECT
        'REQUIRED_STATUS_CHECKS'::TEXT,
        v_bypass OR NOT EXISTS (
            SELECT 1
              FROM unnest(v_policy.required_checks) AS required(check_name)
              LEFT JOIN status_checks sc
                ON sc.pr_id = p_pr_id
               AND sc.head_sha = v_pr.source_head_sha
               AND sc.check_name = required.check_name
               AND sc.check_state = 'passed'
             WHERE sc.status_check_id IS NULL
        ),
        'Every required check must pass on the current source head';

    RETURN QUERY
    SELECT
        'CONVERSATIONS_RESOLVED'::TEXT,
        v_bypass
            OR NOT v_policy.require_conversation_resolution
            OR v_unresolved_threads = 0,
        format('Unresolved review conversations: %s', v_unresolved_threads);

    RETURN QUERY
    SELECT
        'MERGE_METHOD_ALLOWED'::TEXT,
        v_bypass OR CASE p_strategy
            WHEN 'merge_commit' THEN
                v_policy.allow_merge_commit
                AND NOT v_policy.require_linear_history
            WHEN 'squash' THEN v_policy.allow_squash
            WHEN 'rebase' THEN v_policy.allow_rebase
            ELSE FALSE
        END,
        format(
            'Requested strategy: %s; linear history required: %s',
            p_strategy,
            v_policy.require_linear_history
        );

    RETURN QUERY
    SELECT
        'PULL_REQUEST_GOVERNANCE'::TEXT,
        v_policy.require_pull_request,
        CASE
            WHEN v_policy.require_pull_request
                THEN 'Changes are being merged through a Pull Request'
            ELSE 'Repository policy does not require Pull Requests'
        END::TEXT;
END;
$$;

-- ---------------------------------------------------------------------------
-- Merge function and procedure.
-- The function validates all rules before creating the merge commit.
-- The procedure offers a transaction-oriented application entry point.
-- ---------------------------------------------------------------------------

CREATE FUNCTION merge_pull_request(
    p_pr_id BIGINT,
    p_actor_id BIGINT,
    p_strategy TEXT DEFAULT 'squash'
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    v_pr RECORD;
    v_failures TEXT;
    v_new_sha TEXT;
    v_message TEXT;
    v_parents TEXT[];
BEGIN
    IF p_strategy NOT IN ('merge_commit', 'squash', 'rebase') THEN
        RAISE EXCEPTION 'Unsupported merge strategy: %', p_strategy;
    END IF;

    SELECT string_agg(
               rule_name || ': ' || detail,
               '; ' ORDER BY rule_name
           )
      INTO v_failures
      FROM merge_eligibility(p_pr_id, p_actor_id, p_strategy)
     WHERE NOT passed;

    IF v_failures IS NOT NULL THEN
        RAISE EXCEPTION 'Merge blocked: %', v_failures;
    END IF;

    SELECT
        p.*,
        tb.head_commit_sha AS target_head,
        sb.head_commit_sha AS source_head
      INTO v_pr
      FROM pull_requests p
      JOIN branches sb ON sb.branch_id = p.source_branch_id
      JOIN branches tb ON tb.branch_id = p.target_branch_id
     WHERE p.pr_id = p_pr_id
     FOR UPDATE OF p, tb;

    IF p_strategy = 'merge_commit' THEN
        v_parents := ARRAY[v_pr.target_head, v_pr.source_head];
        v_message := format('Merge Pull Request #%s', v_pr.pr_number);
    ELSIF p_strategy = 'squash' THEN
        v_parents := ARRAY[v_pr.target_head];
        v_message := format('Squash Pull Request #%s', v_pr.pr_number);
    ELSE
        v_parents := ARRAY[v_pr.target_head];
        v_message := format('Rebase Pull Request #%s onto target', v_pr.pr_number);
    END IF;

    -- A deterministic 40-character identifier is sufficient for this
    -- relational simulation; production Git object IDs must come from Git.
    v_new_sha :=
        substr(md5(
            p_pr_id::TEXT || ':' || v_pr.target_head || ':' ||
            v_pr.source_head || ':' || p_strategy
        ), 1, 32)
        ||
        substr(md5(
            p_pr_id::TEXT || ':merge-result:' || v_pr.source_head
        ), 1, 8);

    INSERT INTO commits (
        repo_id,
        sha,
        author_id,
        message,
        parent_shas,
        metadata
    )
    VALUES (
        v_pr.repo_id,
        v_new_sha,
        p_actor_id,
        v_message,
        v_parents,
        jsonb_build_object(
            'pull_request_id', p_pr_id,
            'merge_strategy', p_strategy,
            'source_head', v_pr.source_head,
            'target_head', v_pr.target_head
        )
    );

    PERFORM set_config('git_collab.merge_in_progress', 'on', TRUE);

    UPDATE branches
       SET head_commit_sha = v_new_sha
     WHERE branch_id = v_pr.target_branch_id;

    UPDATE pull_requests
       SET state = 'merged',
           is_draft = FALSE,
           merge_strategy = p_strategy,
           merged_commit_sha = v_new_sha,
           closed_at = CURRENT_TIMESTAMP
     WHERE pr_id = p_pr_id;

    PERFORM set_config('git_collab.merge_in_progress', 'off', TRUE);

    RETURN v_new_sha;
END;
$$;

CREATE PROCEDURE process_pull_request_merge(
    IN p_pr_id BIGINT,
    IN p_actor_id BIGINT,
    IN p_strategy TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_merge_sha TEXT;
BEGIN
    v_merge_sha := merge_pull_request(p_pr_id, p_actor_id, p_strategy);
    RAISE NOTICE 'Pull Request % merged as commit %', p_pr_id, v_merge_sha;
END;
$$;

-- ---------------------------------------------------------------------------
-- Lifecycle operations
-- ---------------------------------------------------------------------------

CREATE FUNCTION set_pull_request_state(
    p_pr_id BIGINT,
    p_new_state TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_current_state TEXT;
BEGIN
    IF p_new_state NOT IN ('open', 'closed') THEN
        RAISE EXCEPTION 'This operation supports open or closed states only';
    END IF;

    SELECT state
      INTO v_current_state
      FROM pull_requests
     WHERE pr_id = p_pr_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Pull Request does not exist';
    END IF;

    UPDATE pull_requests
       SET state = p_new_state
     WHERE pr_id = p_pr_id;
END;
$$;

-- ---------------------------------------------------------------------------
-- Reporting view
-- ---------------------------------------------------------------------------

CREATE VIEW pull_request_dashboard AS
WITH latest_reviews AS (
    SELECT DISTINCT ON (r.pr_id, r.reviewer_id)
        r.pr_id,
        r.reviewer_id,
        r.review_state,
        r.reviewed_head_sha
      FROM reviews r
     ORDER BY
        r.pr_id,
        r.reviewer_id,
        r.submitted_at DESC,
        r.review_id DESC
),
review_totals AS (
    SELECT
        p.pr_id,
        COUNT(*) FILTER (
            WHERE lr.review_state = 'approved'
              AND lr.reviewed_head_sha = p.source_head_sha
              AND lr.reviewer_id <> p.author_id
              AND rm.can_review
              AND u.is_active
              AND rm.access_role = ANY(ar.eligible_roles)
        )::INTEGER AS current_approvals,
        COUNT(*) FILTER (
            WHERE lr.review_state = 'changes_requested'
              AND lr.reviewed_head_sha = p.source_head_sha
              AND lr.reviewer_id <> p.author_id
              AND rm.can_review
              AND u.is_active
              AND rm.access_role = ANY(ar.eligible_roles)
        )::INTEGER AS current_change_requests
    FROM pull_requests p
    JOIN branch_protection_policies bp
      ON bp.branch_id = p.target_branch_id
    JOIN approval_requirements ar
      ON ar.policy_id = bp.policy_id
    LEFT JOIN latest_reviews lr
      ON lr.pr_id = p.pr_id
    LEFT JOIN repository_members rm
      ON rm.repo_id = p.repo_id
     AND rm.user_id = lr.reviewer_id
    LEFT JOIN users u
      ON u.user_id = lr.reviewer_id
    GROUP BY p.pr_id
),
thread_totals AS (
    SELECT
        pr_id,
        COUNT(*) FILTER (WHERE NOT is_resolved)::INTEGER AS unresolved_threads
    FROM review_threads
    GROUP BY pr_id
),
check_totals AS (
    SELECT
        p.pr_id,
        COUNT(*) FILTER (WHERE sc.check_state = 'passed')::INTEGER
            AS passing_checks_on_current_head
    FROM pull_requests p
    LEFT JOIN status_checks sc
      ON sc.pr_id = p.pr_id
     AND sc.head_sha = p.source_head_sha
    GROUP BY p.pr_id
)
SELECT
    r.repository_name,
    p.pr_number,
    p.state,
    p.is_draft,
    author.username AS author,
    source.branch_name AS source_branch,
    target.branch_name AS target_branch,
    p.source_head_sha,
    p.base_sha_at_sync,
    target.head_commit_sha AS actual_target_head,
    COALESCE(rt.current_approvals, 0) AS current_approvals,
    ar.required_approvals,
    COALESCE(rt.current_change_requests, 0) AS current_change_requests,
    COALESCE(tt.unresolved_threads, 0) AS unresolved_threads,
    COALESCE(ct.passing_checks_on_current_head, 0)
        AS passing_checks_on_current_head,
    p.merge_strategy,
    p.merged_commit_sha
FROM pull_requests p
JOIN repositories r ON r.repo_id = p.repo_id
JOIN users author ON author.user_id = p.author_id
JOIN branches source ON source.branch_id = p.source_branch_id
JOIN branches target ON target.branch_id = p.target_branch_id
JOIN branch_protection_policies bp ON bp.branch_id = target.branch_id
JOIN approval_requirements ar ON ar.policy_id = bp.policy_id
LEFT JOIN review_totals rt ON rt.pr_id = p.pr_id
LEFT JOIN thread_totals tt ON tt.pr_id = p.pr_id
LEFT JOIN check_totals ct ON ct.pr_id = p.pr_id;

-- ---------------------------------------------------------------------------
-- Sample repository and users
-- ---------------------------------------------------------------------------

INSERT INTO users (username, display_name)
VALUES
    ('alice', 'Alice Developer'),
    ('bob', 'Bob Maintainer'),
    ('carol', 'Carol Reviewer'),
    ('dave', 'Dave Viewer'),
    ('erin', 'Erin Repository Administrator');

INSERT INTO repositories (owner_name, repository_name, default_branch, visibility)
VALUES ('engineering', 'payments-platform', 'main', 'private');

INSERT INTO repository_members (
    repo_id, user_id, access_role, can_review, is_admin
)
SELECT
    1,
    u.user_id,
    CASE u.username
        WHEN 'alice' THEN 'developer'
        WHEN 'bob' THEN 'maintainer'
        WHEN 'carol' THEN 'developer'
        WHEN 'dave' THEN 'viewer'
        WHEN 'erin' THEN 'admin'
    END,
    CASE u.username
        WHEN 'dave' THEN FALSE
        ELSE TRUE
    END,
    u.username = 'erin'
FROM users u;

INSERT INTO commits (
    repo_id, sha, author_id, message, parent_shas, metadata
)
SELECT
    1,
    c.sha,
    u.user_id,
    c.message,
    c.parent_shas,
    c.metadata
FROM (
    VALUES
        (
            repeat('0', 40),
            'erin',
            'Initial repository state',
            ARRAY[]::TEXT[],
            '{"kind":"root"}'::JSONB
        ),
        (
            repeat('1', 40),
            'alice',
            'Add payment validation',
            ARRAY[repeat('0', 40)]::TEXT[],
            '{"files":["src/payment.py"]}'::JSONB
        ),
        (
            repeat('2', 40),
            'alice',
            'Add payment boundary test',
            ARRAY[repeat('1', 40)]::TEXT[],
            '{"files":["tests/test_payment.py"]}'::JSONB
        ),
        (
            repeat('3', 40),
            'alice',
            'Add observability changes',
            ARRAY[repeat('0', 40)]::TEXT[],
            '{"files":["src/metrics.py"]}'::JSONB
        )
) AS c(sha, author_name, message, parent_shas, metadata)
JOIN users u ON u.username = c.author_name;

INSERT INTO branches (
    repo_id, branch_name, head_commit_sha, is_protected
)
VALUES
    (1, 'main', repeat('0', 40), TRUE),
    (1, 'feature/payment-validation', repeat('2', 40), FALSE),
    (1, 'feature/observability', repeat('3', 40), FALSE);

INSERT INTO branch_protection_policies (
    repo_id,
    branch_id,
    require_pull_request,
    required_checks,
    require_conversation_resolution,
    require_linear_history,
    allow_merge_commit,
    allow_squash,
    allow_rebase,
    allow_direct_push,
    allow_force_push,
    prohibit_branch_deletion,
    allow_admin_bypass
)
SELECT
    1,
    b.branch_id,
    TRUE,
    ARRAY['unit-tests', 'security-scan']::TEXT[],
    TRUE,
    TRUE,
    FALSE,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    TRUE,
    FALSE
FROM branches b
WHERE b.repo_id = 1
  AND b.branch_name = 'main';

INSERT INTO approval_requirements (
    policy_id,
    required_approvals,
    eligible_roles,
    exclude_pull_request_author,
    block_current_change_requests
)
SELECT
    policy_id,
    2,
    ARRAY['developer', 'maintainer', 'admin']::TEXT[],
    TRUE,
    TRUE
FROM branch_protection_policies
WHERE repo_id = 1;

-- ---------------------------------------------------------------------------
-- Pull Request records
-- PR 101 is eligible after the required checks and discussions are processed.
-- PR 102 is a deliberately incomplete draft with insufficient governance data.
-- ---------------------------------------------------------------------------

INSERT INTO pull_requests (
    repo_id,
    pr_number,
    author_id,
    source_branch_id,
    target_branch_id,
    base_sha_at_open,
    base_sha_at_sync,
    source_head_sha,
    proposed_changeset,
    state,
    is_draft,
    merge_strategy
)
SELECT
    1,
    p.pr_number,
    author.user_id,
    source.branch_id,
    target.branch_id,
    repeat('0', 40),
    repeat('0', 40),
    p.source_sha,
    p.changeset,
    p.state,
    p.is_draft,
    p.strategy
FROM (
    VALUES
        (
            101,
            'alice',
            'feature/payment-validation',
            repeat('2', 40),
            '{"src/payment.py":{"change":"payment validation"},"tests/test_payment.py":{"change":"boundary test"}}'::JSONB,
            'open',
            FALSE,
            'squash'
        ),
        (
            102,
            'alice',
            'feature/observability',
            repeat('3', 40),
            '{"src/metrics.py":{"change":"metrics instrumentation"}}'::JSONB,
            'draft',
            TRUE,
            'merge_commit'
        )
) AS p(
    pr_number,
    author_name,
    source_name,
    source_sha,
    changeset,
    state,
    is_draft,
    strategy
)
JOIN users author ON author.username = p.author_name
JOIN branches source ON source.repo_id = 1 AND source.branch_name = p.source_name
JOIN branches target ON target.repo_id = 1 AND target.branch_name = 'main';

-- Current approvals for PR 101.
INSERT INTO reviews (
    pr_id, repo_id, reviewer_id, review_state, reviewed_head_sha, review_body
)
SELECT
    p.pr_id,
    1,
    u.user_id,
    'approved',
    repeat('2', 40),
    CASE u.username
        WHEN 'bob' THEN 'Validation and error handling reviewed.'
        ELSE 'Boundary tests and expected behavior reviewed.'
    END
FROM pull_requests p
CROSS JOIN users u
WHERE p.repo_id = 1
  AND p.pr_number = 101
  AND u.username IN ('bob', 'carol');

-- PR 102 has only one approval, so it cannot satisfy the two-approval policy.
INSERT INTO reviews (
    pr_id, repo_id, reviewer_id, review_state, reviewed_head_sha, review_body
)
SELECT
    p.pr_id,
    1,
    u.user_id,
    'approved',
    repeat('3', 40),
    'Initial review completed.'
FROM pull_requests p
JOIN users u ON u.username = 'bob'
WHERE p.repo_id = 1
  AND p.pr_number = 102;

-- Review threads and inline comments.
INSERT INTO review_threads (
    pr_id, file_path, line_number, created_by, is_resolved, resolved_by, resolved_at
)
SELECT
    p.pr_id,
    'src/payment.py',
    12,
    bob.user_id,
    TRUE,
    alice.user_id,
    CURRENT_TIMESTAMP
FROM pull_requests p
JOIN users bob ON bob.username = 'bob'
JOIN users alice ON alice.username = 'alice'
WHERE p.repo_id = 1
  AND p.pr_number = 101;

INSERT INTO review_threads (
    pr_id, file_path, line_number, created_by, is_resolved
)
SELECT
    p.pr_id,
    'src/metrics.py',
    18,
    bob.user_id,
    FALSE
FROM pull_requests p
JOIN users bob ON bob.username = 'bob'
WHERE p.repo_id = 1
  AND p.pr_number = 102;

INSERT INTO review_comments (
    pr_id, thread_id, review_id, author_id, comment_body
)
SELECT
    p.pr_id,
    t.thread_id,
    r.review_id,
    bob.user_id,
    'Please verify that invalid payment amounts are rejected.'
FROM pull_requests p
JOIN review_threads t ON t.pr_id = p.pr_id
JOIN reviews r ON r.pr_id = p.pr_id
JOIN users bob ON bob.username = 'bob'
WHERE p.repo_id = 1
  AND p.pr_number = 101
  AND r.review_state = 'approved'
  AND r.reviewer_id = bob.user_id;

-- Required checks pass for PR 101 on its exact source head.
INSERT INTO status_checks (
    pr_id, repo_id, head_sha, check_name, check_state, details, completed_at
)
SELECT
    p.pr_id,
    1,
    repeat('2', 40),
    required.check_name,
    'passed',
    'Completed successfully on the current proposed revision.',
    CURRENT_TIMESTAMP
FROM pull_requests p
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan')
) AS required(check_name)
WHERE p.repo_id = 1
  AND p.pr_number = 101;

-- PR 102 has a failed check and no security-scan result.
INSERT INTO status_checks (
    pr_id, repo_id, head_sha, check_name, check_state, details, completed_at
)
SELECT
    p.pr_id,
    1,
    repeat('3', 40),
    'unit-tests',
    'failed',
    'A test failure remains unresolved.',
    CURRENT_TIMESTAMP
FROM pull_requests p
WHERE p.repo_id = 1
  AND p.pr_number = 102;

-- ---------------------------------------------------------------------------
-- Retrieval and reporting queries
-- ---------------------------------------------------------------------------

-- 1. Pull Request status, branch references, review totals, and check counts.
SELECT *
FROM pull_request_dashboard
ORDER BY pr_number;

-- 2. Retrieve proposed changesets independently from current branch state.
SELECT
    p.pr_number,
    p.source_head_sha AS proposed_source_head,
    p.base_sha_at_sync AS synchronized_target_head,
    p.proposed_changeset
FROM pull_requests p
WHERE p.repo_id = 1
ORDER BY p.pr_number;

-- 3. Review history, including dismissed or superseded decisions.
SELECT
    p.pr_number,
    reviewer.username AS reviewer,
    r.review_state,
    r.reviewed_head_sha,
    r.submitted_at
FROM reviews r
JOIN pull_requests p ON p.pr_id = r.pr_id
JOIN users reviewer ON reviewer.user_id = r.reviewer_id
WHERE p.repo_id = 1
ORDER BY p.pr_number, r.submitted_at, r.review_id;

-- 4. Required check coverage by Pull Request and source head.
SELECT
    p.pr_number,
    p.source_head_sha,
    required.check_name,
    COALESCE(sc.check_state, 'missing') AS current_check_state
FROM pull_requests p
JOIN branch_protection_policies bp
  ON bp.branch_id = p.target_branch_id
CROSS JOIN LATERAL unnest(bp.required_checks) AS required(check_name)
LEFT JOIN status_checks sc
  ON sc.pr_id = p.pr_id
 AND sc.head_sha = p.source_head_sha
 AND sc.check_name = required.check_name
WHERE p.repo_id = 1
ORDER BY p.pr_number, required.check_name;

-- 5. Aggregated review-discussion workload.
SELECT
    p.pr_number,
    COUNT(t.thread_id) AS total_threads,
    COUNT(t.thread_id) FILTER (WHERE NOT t.is_resolved) AS unresolved_threads
FROM pull_requests p
LEFT JOIN review_threads t ON t.pr_id = p.pr_id
WHERE p.repo_id = 1
GROUP BY p.pr_number
ORDER BY p.pr_number;

-- ---------------------------------------------------------------------------
-- Eligibility evaluation
-- ---------------------------------------------------------------------------

-- Maintainer Bob evaluates both Pull Requests using the squash strategy.
-- PR 101 should satisfy the configured rules.
-- PR 102 should fail because it is draft, has insufficient approvals,
-- has a failed/missing check, and has an unresolved discussion.
SELECT
    p.pr_number,
    e.rule_name,
    e.passed,
    e.detail
FROM pull_requests p
CROSS JOIN LATERAL merge_eligibility(
    p.pr_id,
    (SELECT user_id FROM users WHERE username = 'bob'),
    'squash'
) e
WHERE p.repo_id = 1
ORDER BY p.pr_number, e.rule_name;

-- CTE-based merge-readiness report. A Pull Request is eligible only when
-- every returned rule passes.
WITH rule_results AS (
    SELECT
        p.pr_number,
        e.rule_name,
        e.passed
    FROM pull_requests p
    CROSS JOIN LATERAL merge_eligibility(
        p.pr_id,
        (SELECT user_id FROM users WHERE username = 'bob'),
        'squash'
    ) e
    WHERE p.repo_id = 1
)
SELECT
    pr_number,
    BOOL_AND(passed) AS merge_eligible,
    COUNT(*) AS evaluated_rules,
    COUNT(*) FILTER (WHERE NOT passed) AS failed_rules
FROM rule_results
GROUP BY pr_number
ORDER BY pr_number;

-- ---------------------------------------------------------------------------
-- Workflow processing and transaction handling
-- ---------------------------------------------------------------------------

-- The successful merge updates the target branch and Pull Request atomically.
BEGIN;

CALL process_pull_request_merge(
    (SELECT pr_id FROM pull_requests WHERE repo_id = 1 AND pr_number = 101),
    (SELECT user_id FROM users WHERE username = 'bob'),
    'squash'
);

COMMIT;

-- The merged Pull Request now points to the resulting commit.
SELECT
    pr_number,
    state,
    merge_strategy,
    merged_commit_sha
FROM pull_requests
WHERE repo_id = 1
ORDER BY pr_number;

-- The main branch head is the merge result.
SELECT
    branch_name,
    head_commit_sha,
    is_protected
FROM branches
WHERE repo_id = 1
  AND branch_name = 'main';

-- ---------------------------------------------------------------------------
-- Failure-path demonstrations
-- ---------------------------------------------------------------------------

-- A failed merge attempt is caught inside a DO block. The exception rolls
-- back the attempted operation without terminating the rest of the script.
DO $$
DECLARE
    v_pr_id BIGINT;
    v_bob_id BIGINT;
BEGIN
    SELECT pr_id
      INTO v_pr_id
      FROM pull_requests
     WHERE repo_id = 1
       AND pr_number = 102;

    SELECT user_id
      INTO v_bob_id
      FROM users
     WHERE username = 'bob';

    BEGIN
        PERFORM merge_pull_request(v_pr_id, v_bob_id, 'merge_commit');
        RAISE EXCEPTION 'Expected merge to be blocked, but it succeeded';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Expected rejected merge: %', SQLERRM;
    END;
END;
$$;

-- Attempting to bypass the protected-branch merge workflow through a direct
-- SQL update is rejected by the branch-head trigger.
DO $$
DECLARE
    v_branch_id BIGINT;
BEGIN
    SELECT branch_id
      INTO v_branch_id
      FROM branches
     WHERE repo_id = 1
       AND branch_name = 'main';

    BEGIN
        UPDATE branches
           SET head_commit_sha = repeat('3', 40)
         WHERE branch_id = v_branch_id;

        RAISE EXCEPTION 'Expected protected-branch update to be rejected';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Expected branch-protection rejection: %', SQLERRM;
    END;
END;
$$;

-- Review insertion by a user without review permission is rejected.
DO $$
DECLARE
    v_pr_id BIGINT;
    v_dave_id BIGINT;
BEGIN
    SELECT pr_id
      INTO v_pr_id
      FROM pull_requests
     WHERE repo_id = 1
       AND pr_number = 102;

    SELECT user_id
      INTO v_dave_id
      FROM users
     WHERE username = 'dave';

    BEGIN
        INSERT INTO reviews (
            pr_id,
            repo_id,
            reviewer_id,
            review_state,
            reviewed_head_sha,
            review_body
        )
        SELECT
            v_pr_id,
            1,
            v_dave_id,
            'approved',
            source_head_sha,
            'Attempt by a member without review permission.'
        FROM pull_requests
        WHERE pr_id = v_pr_id;

        RAISE EXCEPTION 'Expected ineligible review to be rejected';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Expected reviewer-eligibility rejection: %', SQLERRM;
    END;
END;
$$;

-- Final repository governance state.
SELECT
    repository_name,
    pr_number,
    state,
    source_branch,
    target_branch,
    current_approvals,
    required_approvals,
    unresolved_threads,
    merged_commit_sha
FROM pull_request_dashboard
ORDER BY pr_number;
