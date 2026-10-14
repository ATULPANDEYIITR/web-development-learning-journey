-- Error handling in PostgreSQL through repository governance.
--
-- This script models database-level validation, exception translation,
-- transaction rollback, audit logging, and controlled failure recovery.
-- Execute in a disposable PostgreSQL database with psql.
--
-- PL/pgSQL exception blocks create subtransactions. If a statement fails
-- inside a block's protected section, its database changes are rolled back
-- before the handler runs. The surrounding transaction can then continue.

BEGIN;

DROP SCHEMA IF EXISTS error_handling_demo CASCADE;
CREATE SCHEMA error_handling_demo;
SET LOCAL search_path = error_handling_demo, public;

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

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL DEFAULT 'main',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(repository_name)) > 0),
    CHECK (length(trim(default_branch)) > 0)
);

CREATE TABLE repository_members (
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    username TEXT NOT NULL,
    can_review BOOLEAN NOT NULL DEFAULT FALSE,
    is_administrator BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (repository_id, username),
    CHECK (length(trim(username)) > 0)
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    head_commit TEXT NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (branch_id),
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) > 0),
    CHECK (length(trim(head_commit)) > 0)
);

CREATE TABLE branch_protection (
    protection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    required_approvals INTEGER NOT NULL DEFAULT 1,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    prohibit_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    prohibit_force_push BOOLEAN NOT NULL DEFAULT TRUE,
    prohibit_deletion BOOLEAN NOT NULL DEFAULT TRUE,
    dismiss_stale_approvals BOOLEAN NOT NULL DEFAULT TRUE,
    administrators_may_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) > 0),
    CHECK (required_approvals >= 0)
);

CREATE TABLE required_status_checks (
    protection_id BIGINT NOT NULL REFERENCES branch_protection(protection_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (protection_id, check_name),
    CHECK (length(trim(check_name)) > 0)
);

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    author TEXT NOT NULL,
    title TEXT NOT NULL,
    source_branch TEXT NOT NULL,
    target_branch TEXT NOT NULL,
    head_commit TEXT NOT NULL,
    state pull_request_state NOT NULL DEFAULT 'draft',
    has_merge_conflict BOOLEAN NOT NULL DEFAULT FALSE,
    unresolved_conversations INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    merged_at TIMESTAMPTZ,
    CHECK (length(trim(author)) > 0),
    CHECK (length(trim(title)) > 0),
    CHECK (length(trim(source_branch)) > 0),
    CHECK (length(trim(target_branch)) > 0),
    CHECK (source_branch <> target_branch),
    CHECK (length(trim(head_commit)) > 0),
    CHECK (unresolved_conversations >= 0),
    CHECK (
        (state = 'merged' AND merged_at IS NOT NULL)
        OR (state <> 'merged' AND merged_at IS NULL)
    )
);

CREATE INDEX idx_pull_requests_repository_state
    ON pull_requests(repository_id, state);

CREATE INDEX idx_pull_requests_target_branch
    ON pull_requests(repository_id, target_branch);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    commit_hash TEXT NOT NULL,
    commit_position INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_hash),
    UNIQUE (pull_request_id, commit_position),
    CHECK (length(trim(commit_hash)) > 0),
    CHECK (commit_position > 0)
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer TEXT NOT NULL,
    state review_state NOT NULL,
    reviewed_commit TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    dismissed_at TIMESTAMPTZ,
    CHECK (length(trim(reviewer)) > 0),
    CHECK (length(trim(reviewed_commit)) > 0),
    CHECK (
        (state = 'dismissed' AND dismissed_at IS NOT NULL)
        OR (state <> 'dismissed' AND dismissed_at IS NULL)
    )
);

CREATE INDEX idx_reviews_pull_request_reviewer
    ON reviews(pull_request_id, reviewer, submitted_at DESC);

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(review_id)
        ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    comment_body TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(file_path)) > 0),
    CHECK (line_number IS NULL OR line_number > 0),
    CHECK (length(trim(comment_body)) > 0)
);

CREATE INDEX idx_review_comments_unresolved
    ON review_comments(review_id)
    WHERE is_resolved = FALSE;

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state check_state NOT NULL DEFAULT 'pending',
    tested_commit TEXT NOT NULL,
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name, tested_commit),
    CHECK (length(trim(check_name)) > 0),
    CHECK (length(trim(tested_commit)) > 0),
    CHECK (
        (state = 'passed' AND completed_at IS NOT NULL)
        OR (state <> 'passed' AND completed_at IS NULL)
    )
);

CREATE INDEX idx_status_checks_current_commit
    ON status_checks(pull_request_id, tested_commit, check_name);

CREATE TABLE governance_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT REFERENCES repositories(repository_id)
        ON DELETE SET NULL,
    pull_request_id BIGINT REFERENCES pull_requests(pull_request_id)
        ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    sqlstate_code TEXT,
    message TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(event_type)) > 0),
    CHECK (length(trim(message)) > 0)
);

CREATE FUNCTION validate_review_submission()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_author TEXT;
    v_repository_id BIGINT;
    v_can_review BOOLEAN;
BEGIN
    SELECT author, repository_id
      INTO v_author, v_repository_id
      FROM pull_requests
     WHERE pull_request_id = NEW.pull_request_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = 'P0002',
            MESSAGE = 'Pull request does not exist';
    END IF;

    IF NEW.reviewer = v_author THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'Pull request authors cannot approve their own changes';
    END IF;

    SELECT can_review
      INTO v_can_review
      FROM repository_members
     WHERE repository_id = v_repository_id
       AND username = NEW.reviewer;

    IF NOT FOUND OR NOT v_can_review THEN
        RAISE EXCEPTION USING
            ERRCODE = '42501',
            MESSAGE = 'Reviewer is not eligible for this repository';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_review_submission
BEFORE INSERT OR UPDATE ON reviews
FOR EACH ROW
EXECUTE FUNCTION validate_review_submission();

CREATE FUNCTION validate_pull_request_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state = 'merged' AND NEW.state <> 'merged' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'A merged pull request cannot be reopened or closed';
    END IF;

    IF OLD.state = 'draft' AND NEW.state NOT IN ('open', 'closed', 'draft') THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'A draft pull request cannot transition directly to merged';
    END IF;

    IF OLD.state = 'closed' AND NEW.state NOT IN ('open', 'closed') THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'A closed pull request must be reopened before merging';
    END IF;

    IF NEW.state = 'merged' AND OLD.state <> 'open' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'Only an open pull request can be merged';
    END IF;

    IF NEW.state = 'merged' AND NEW.merged_at IS NULL THEN
        NEW.merged_at := now();
    END IF;

    IF NEW.state <> 'merged' THEN
        NEW.merged_at := NULL;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_pull_request_transition
BEFORE UPDATE OF state ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION validate_pull_request_transition();

CREATE FUNCTION merge_blockers(p_pull_request_id BIGINT)
RETURNS TABLE(blocker TEXT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_pr pull_requests%ROWTYPE;
    v_protection branch_protection%ROWTYPE;
    v_protection_id BIGINT;
    v_approval_count INTEGER;
    v_changes_requested BOOLEAN;
    v_check RECORD;
BEGIN
    SELECT *
      INTO v_pr
      FROM pull_requests
     WHERE pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = 'P0002',
            MESSAGE = format('Pull request %s does not exist', p_pull_request_id);
    END IF;

    IF v_pr.state <> 'open' THEN
        RETURN QUERY SELECT 'Pull request is not open'::TEXT;
    END IF;

    IF v_pr.has_merge_conflict THEN
        RETURN QUERY SELECT 'Merge conflicts remain unresolved'::TEXT;
    END IF;

    SELECT *
      INTO v_protection
      FROM branch_protection
     WHERE repository_id = v_pr.repository_id
       AND branch_name = v_pr.target_branch;

    IF NOT FOUND THEN
        RETURN QUERY SELECT 'Target branch has no protection policy'::TEXT;
        RETURN;
    END IF;

    v_protection_id := v_protection.protection_id;

    SELECT count(DISTINCT rv.reviewer)::INTEGER
      INTO v_approval_count
      FROM reviews rv
      JOIN repository_members rm
        ON rm.repository_id = v_pr.repository_id
       AND rm.username = rv.reviewer
       AND rm.can_review
     WHERE rv.pull_request_id = p_pull_request_id
       AND rv.state = 'approved'
       AND rv.reviewer <> v_pr.author
       AND (
           NOT v_protection.dismiss_stale_approvals
           OR rv.reviewed_commit = v_pr.head_commit
       );

    IF v_approval_count < v_protection.required_approvals THEN
        RETURN QUERY SELECT format(
            'Insufficient approvals: %s of %s',
            v_approval_count,
            v_protection.required_approvals
        );
    END IF;

    SELECT EXISTS (
        SELECT 1
          FROM reviews rv
          JOIN repository_members rm
            ON rm.repository_id = v_pr.repository_id
           AND rm.username = rv.reviewer
           AND rm.can_review
         WHERE rv.pull_request_id = p_pull_request_id
           AND rv.state = 'changes_requested'
           AND rv.reviewer <> v_pr.author
           AND (
               NOT v_protection.dismiss_stale_approvals
               OR rv.reviewed_commit = v_pr.head_commit
           )
    )
    INTO v_changes_requested;

    IF v_changes_requested THEN
        RETURN QUERY SELECT
            'An eligible reviewer has requested changes'::TEXT;
    END IF;

    FOR v_check IN
        SELECT rsc.check_name
          FROM required_status_checks rsc
         WHERE rsc.protection_id = v_protection_id
    LOOP
        IF NOT EXISTS (
            SELECT 1
              FROM status_checks sc
             WHERE sc.pull_request_id = p_pull_request_id
               AND sc.check_name = v_check.check_name
               AND sc.tested_commit = v_pr.head_commit
               AND sc.state = 'passed'
               AND sc.completed_at IS NOT NULL
        ) THEN
            RETURN QUERY SELECT format(
                'Required check is missing, stale, or unsuccessful: %s',
                v_check.check_name
            );
        END IF;
    END LOOP;

    IF v_protection.require_conversation_resolution
       AND v_pr.unresolved_conversations > 0 THEN
        RETURN QUERY SELECT format(
            '%s review conversation(s) remain unresolved',
            v_pr.unresolved_conversations
        );
    END IF;

    IF v_protection.require_linear_history THEN
        RETURN QUERY SELECT
            'Linear history must be verified by the Git hosting layer'::TEXT;
    END IF;
END;
$$;

CREATE FUNCTION attempt_merge(p_pull_request_id BIGINT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_blockers TEXT;
    v_repository_id BIGINT;
BEGIN
    SELECT repository_id
      INTO v_repository_id
      FROM pull_requests
     WHERE pull_request_id = p_pull_request_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = 'P0002',
            MESSAGE = format('Pull request %s does not exist', p_pull_request_id);
    END IF;

    SELECT string_agg(blocker, '; ' ORDER BY blocker)
      INTO v_blockers
      FROM merge_blockers(p_pull_request_id);

    IF v_blockers IS NOT NULL THEN
        INSERT INTO governance_events (
            repository_id,
            pull_request_id,
            event_type,
            sqlstate_code,
            message
        )
        VALUES (
            v_repository_id,
            p_pull_request_id,
            'merge_rejected',
            'P0001',
            v_blockers
        );

        RAISE EXCEPTION USING
            ERRCODE = 'P0001',
            MESSAGE = 'Merge denied: ' || v_blockers;
    END IF;

    UPDATE pull_requests
       SET state = 'merged',
           merged_at = now()
     WHERE pull_request_id = p_pull_request_id;

    INSERT INTO governance_events (
        repository_id,
        pull_request_id,
        event_type,
        message
    )
    VALUES (
        v_repository_id,
        p_pull_request_id,
        'merge_succeeded',
        'All modeled merge requirements passed.'
    );
END;
$$;

INSERT INTO repositories (repository_name, default_branch)
VALUES ('platform-service', 'main');

INSERT INTO repository_members (
    repository_id, username, can_review, is_administrator
)
SELECT repository_id, username, can_review, is_administrator
FROM repositories
CROSS JOIN (
    VALUES
        ('developer-alex', FALSE, FALSE),
        ('developer-jules', FALSE, FALSE),
        ('reviewer-mira', TRUE, FALSE),
        ('reviewer-sam', TRUE, FALSE),
        ('release-admin', TRUE, TRUE)
) AS members(username, can_review, is_administrator)
WHERE repository_name = 'platform-service';

INSERT INTO branches (repository_id, branch_name, head_commit)
SELECT repository_id, branch_name, head_commit
FROM repositories
CROSS JOIN (
    VALUES
        ('main', 'base-a01'),
        ('feature/release-validation', 'commit-a91'),
        ('feature/credential-update', 'commit-b72')
) AS branch_data(branch_name, head_commit)
WHERE repository_name = 'platform-service';

INSERT INTO branch_protection (
    repository_id,
    branch_name,
    required_approvals,
    require_conversation_resolution,
    require_linear_history,
    prohibit_direct_push,
    prohibit_force_push,
    prohibit_deletion,
    dismiss_stale_approvals,
    administrators_may_bypass
)
SELECT
    repository_id,
    'main',
    2,
    TRUE,
    FALSE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    FALSE
FROM repositories
WHERE repository_name = 'platform-service';

INSERT INTO required_status_checks (protection_id, check_name)
SELECT protection_id, check_name
FROM branch_protection
CROSS JOIN (
    VALUES ('build'), ('unit-tests'), ('security-scan')
) AS required(check_name)
WHERE branch_name = 'main';

INSERT INTO pull_requests (
    repository_id,
    author,
    title,
    source_branch,
    target_branch,
    head_commit,
    state
)
SELECT repository_id,
       'developer-alex',
       'Validate release configuration',
       'feature/release-validation',
       'main',
       'commit-a91',
       'open'
FROM repositories
WHERE repository_name = 'platform-service';

INSERT INTO pull_requests (
    repository_id,
    author,
    title,
    source_branch,
    target_branch,
    head_commit,
    state,
    has_merge_conflict,
    unresolved_conversations
)
SELECT repository_id,
       'developer-jules',
       'Update deployment credentials',
       'feature/credential-update',
       'main',
       'commit-b72',
       'open',
       TRUE,
       2
FROM repositories
WHERE repository_name = 'platform-service';

INSERT INTO pull_request_commits (
    pull_request_id, commit_hash, commit_position
)
SELECT pull_request_id, head_commit, 1
FROM pull_requests;

INSERT INTO reviews (
    pull_request_id, reviewer, state, reviewed_commit
)
SELECT pr.pull_request_id, rv.reviewer, rv.state, rv.reviewed_commit
FROM pull_requests pr
JOIN repositories repo USING (repository_id)
CROSS JOIN (
    VALUES
        ('reviewer-mira', 'approved'::review_state, 'commit-a91'),
        ('reviewer-sam', 'approved'::review_state, 'commit-a91'),
        ('reviewer-mira', 'approved'::review_state, 'commit-b70'),
        ('reviewer-sam', 'changes_requested'::review_state, 'commit-b72'),
        ('developer-jules', 'approved'::review_state, 'commit-b72')
) AS rv(reviewer, state, reviewed_commit)
WHERE repo.repository_name = 'platform-service'
  AND (
      (pr.title = 'Validate release configuration'
       AND rv.reviewed_commit = 'commit-a91')
      OR
      (pr.title = 'Update deployment credentials'
       AND rv.reviewed_commit <> 'commit-a91')
  )
  AND rv.reviewer <> pr.author
  AND EXISTS (
      SELECT 1
      FROM repository_members rm
      WHERE rm.repository_id = pr.repository_id
        AND rm.username = rv.reviewer
        AND rm.can_review
  );

INSERT INTO review_comments (
    review_id, file_path, line_number, comment_body, is_resolved
)
SELECT review_id,
       'deployment/config.yml',
       18,
       'Confirm that deployment credentials are sourced from the approved secret store.',
       FALSE
FROM reviews
WHERE state = 'changes_requested';

INSERT INTO status_checks (
    pull_request_id, check_name, state, tested_commit, completed_at
)
SELECT pr.pull_request_id,
       check_data.check_name,
       check_data.state,
       check_data.commit_hash,
       CASE
           WHEN check_data.state = 'passed' THEN now()
           ELSE NULL
       END
FROM pull_requests pr
CROSS JOIN (
    VALUES
        ('build', 'passed'::check_state, 'commit-a91'),
        ('unit-tests', 'passed'::check_state, 'commit-a91'),
        ('security-scan', 'passed'::check_state, 'commit-a91'),
        ('build', 'passed'::check_state, 'commit-b72'),
        ('unit-tests', 'pending'::check_state, 'commit-b72')
) AS check_data(check_name, state, commit_hash)
WHERE
    (pr.title = 'Validate release configuration' AND check_data.commit_hash = 'commit-a91')
    OR
    (pr.title = 'Update deployment credentials' AND check_data.commit_hash = 'commit-b72');

-- Inspect modeled blockers without raising an exception.
SELECT pr.pull_request_id,
       pr.title,
       mb.blocker
FROM pull_requests pr
CROSS JOIN LATERAL merge_blockers(pr.pull_request_id) AS mb
ORDER BY pr.pull_request_id, mb.blocker;

-- A failed merge attempt is isolated in a PL/pgSQL exception block.
-- The failed attempt's changes are rolled back to the block savepoint, but
-- the handler's diagnostic record is retained in the surrounding transaction.
DO $$
BEGIN
    BEGIN
        PERFORM attempt_merge(
            (
                SELECT pull_request_id
                FROM pull_requests
                WHERE title = 'Update deployment credentials'
            )
        );
    EXCEPTION
        WHEN SQLSTATE 'P0001' THEN
            RAISE NOTICE 'Expected policy rejection: %', SQLERRM;
        WHEN OTHERS THEN
            RAISE NOTICE 'Unexpected SQL failure [%]: %', SQLSTATE, SQLERRM;
    END;
END;
$$;

-- Correct the blocked request, then reevaluate it against the current head.
UPDATE pull_requests
SET has_merge_conflict = FALSE,
    unresolved_conversations = 0
WHERE title = 'Update deployment credentials';

UPDATE reviews
SET state = 'approved'
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE title = 'Update deployment credentials'
)
AND reviewer = 'reviewer-sam';

UPDATE status_checks
SET state = 'passed',
    completed_at = now()
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE title = 'Update deployment credentials'
)
AND check_name = 'unit-tests'
AND tested_commit = 'commit-b72';

-- A second approval is still needed because the only other approved review
-- belongs to an ineligible author, while the older approval is stale.
INSERT INTO reviews (
    pull_request_id, reviewer, state, reviewed_commit
)
SELECT pull_request_id, 'release-admin', 'approved', head_commit
FROM pull_requests
WHERE title = 'Update deployment credentials';

SELECT pr.pull_request_id,
       pr.title,
       count(mb.blocker) AS remaining_blocker_count
FROM pull_requests pr
LEFT JOIN LATERAL merge_blockers(pr.pull_request_id) mb ON TRUE
GROUP BY pr.pull_request_id, pr.title
ORDER BY pr.pull_request_id;

-- Demonstrate the database's review-eligibility validation. The exception
-- handler allows the rest of the educational script to continue.
DO $$
DECLARE
    v_pr_id BIGINT;
BEGIN
    SELECT pull_request_id
      INTO v_pr_id
      FROM pull_requests
     WHERE title = 'Validate release configuration';

    BEGIN
        INSERT INTO reviews (
            pull_request_id, reviewer, state, reviewed_commit
        )
        VALUES (v_pr_id, 'developer-alex', 'approved', 'commit-a91');
    EXCEPTION
        WHEN check_violation OR insufficient_privilege THEN
            RAISE NOTICE 'Expected reviewer validation failure: %', SQLERRM;
        WHEN OTHERS THEN
            RAISE NOTICE 'Unexpected review insertion failure [%]: %',
                SQLSTATE, SQLERRM;
    END;
END;
$$;

-- Attempt the valid merge after repairing the blocked request.
DO $$
DECLARE
    v_pr_id BIGINT;
BEGIN
    SELECT pull_request_id
      INTO v_pr_id
      FROM pull_requests
     WHERE title = 'Update deployment credentials';

    BEGIN
        PERFORM attempt_merge(v_pr_id);
        RAISE NOTICE 'Pull request % merged successfully.', v_pr_id;
    EXCEPTION
        WHEN SQLSTATE 'P0001' THEN
            RAISE NOTICE 'Merge still blocked: %', SQLERRM;
    END;
END;
$$;

-- Operational diagnostics distinguish merge decisions from unexpected errors.
SELECT event_type, sqlstate_code, message, occurred_at
FROM governance_events
ORDER BY event_id;

SELECT pull_request_id, title, state, merged_at
FROM pull_requests
ORDER BY pull_request_id;

COMMIT;
