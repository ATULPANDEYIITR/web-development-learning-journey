-- PostgreSQL 15+
-- Repository governance: Pull Requests, reviews, approvals, and protection.
-- This schema uses immutable review history and explicit merge-eligibility
-- queries. It does not pretend that SQL has JavaScript's dynamic this.

BEGIN;

DROP VIEW IF EXISTS pull_request_merge_eligibility CASCADE;
DROP TABLE IF EXISTS merge_events CASCADE;
DROP TABLE IF EXISTS status_checks CASCADE;
DROP TABLE IF EXISTS review_comments CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS pull_request_commits CASCADE;
DROP TABLE IF EXISTS commits CASCADE;
DROP TABLE IF EXISTS pull_requests CASCADE;
DROP TABLE IF EXISTS branch_protection CASCADE;
DROP TABLE IF EXISTS branches CASCADE;
DROP TABLE IF EXISTS repository_members CASCADE;
DROP TABLE IF EXISTS repositories CASCADE;

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_name TEXT NOT NULL,
    repository_name TEXT NOT NULL,
    default_branch TEXT NOT NULL DEFAULT 'main',
    UNIQUE (owner_name, repository_name),
    CHECK (length(trim(owner_name)) > 0),
    CHECK (length(trim(repository_name)) > 0)
);

CREATE TABLE repository_members (
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    role_name TEXT NOT NULL
        CHECK (role_name IN ('AUTHOR', 'CONTRIBUTOR', 'REVIEWER', 'MAINTAINER', 'ADMIN')),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (repository_id, username)
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    head_sha CHAR(40) NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name),
    CHECK (branch_name !~ '\s'),
    CHECK (head_sha ~ '^[0-9a-f]{40}$')
);

CREATE TABLE branch_protection (
    protection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE
        REFERENCES branches(branch_id) ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 1
        CHECK (required_approvals >= 0),
    require_code_owner_review BOOLEAN NOT NULL DEFAULT FALSE,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    require_up_to_date_branch BOOLEAN NOT NULL DEFAULT TRUE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    restrict_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    dismiss_stale_approvals BOOLEAN NOT NULL DEFAULT TRUE,
    allow_admin_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    allowed_merge_methods TEXT[] NOT NULL
        DEFAULT ARRAY['MERGE', 'SQUASH']::TEXT[],
    required_check_names TEXT[] NOT NULL
        DEFAULT ARRAY['ci-tests', 'security-scan']::TEXT[],
    CHECK (
        allowed_merge_methods <@ ARRAY['MERGE', 'SQUASH', 'REBASE']::TEXT[]
    ),
    CHECK (cardinality(required_check_names) > 0)
);

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    pr_number INTEGER NOT NULL CHECK (pr_number > 0),
    author_username TEXT NOT NULL,
    source_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    description TEXT NOT NULL DEFAULT '',
    lifecycle_state TEXT NOT NULL DEFAULT 'OPEN'
        CHECK (lifecycle_state IN ('DRAFT', 'OPEN', 'CLOSED', 'MERGED')),
    merge_method TEXT
        CHECK (merge_method IN ('MERGE', 'SQUASH', 'REBASE')),
    base_synchronized BOOLEAN NOT NULL DEFAULT FALSE,
    has_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ,
    merged_at TIMESTAMPTZ,
    UNIQUE (repository_id, pr_number),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (
        (lifecycle_state = 'MERGED' AND merged_at IS NOT NULL)
        OR lifecycle_state <> 'MERGED'
    )
);

CREATE TABLE commits (
    commit_sha CHAR(40) PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    author_username TEXT NOT NULL,
    commit_message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (commit_sha ~ '^[0-9a-f]{40}$'),
    CHECK (length(trim(commit_message)) > 0)
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    commit_sha CHAR(40) NOT NULL
        REFERENCES commits(commit_sha),
    position INTEGER NOT NULL CHECK (position > 0),
    PRIMARY KEY (pull_request_id, commit_sha),
    UNIQUE (pull_request_id, position)
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    reviewer_username TEXT NOT NULL,
    review_state TEXT NOT NULL
        CHECK (review_state IN ('COMMENTED', 'APPROVED', 'CHANGES_REQUESTED', 'DISMISSED')),
    commit_sha CHAR(40),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    dismissed_at TIMESTAMPTZ,
    CHECK (
        (review_state = 'DISMISSED' AND dismissed_at IS NOT NULL)
        OR review_state <> 'DISMISSED'
    )
);

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES reviews(review_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER CHECK (line_number IS NULL OR line_number > 0),
    comment_body TEXT NOT NULL CHECK (length(trim(comment_body)) > 0),
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    check_state TEXT NOT NULL
        CHECK (check_state IN ('PENDING', 'SUCCESS', 'FAILURE', 'CANCELLED')),
    checked_commit_sha CHAR(40),
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name),
    CHECK (
        (check_state = 'PENDING' AND completed_at IS NULL)
        OR (check_state <> 'PENDING')
    )
);

CREATE TABLE merge_events (
    merge_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL UNIQUE
        REFERENCES pull_requests(pull_request_id),
    merged_by TEXT NOT NULL,
    merge_method TEXT NOT NULL
        CHECK (merge_method IN ('MERGE', 'SQUASH', 'REBASE')),
    merged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resulting_commit_sha CHAR(40)
);

CREATE INDEX idx_pull_requests_repository_state
    ON pull_requests(repository_id, lifecycle_state);

CREATE INDEX idx_reviews_pr_state_time
    ON reviews(pull_request_id, review_state, submitted_at DESC);

CREATE INDEX idx_review_comments_unresolved
    ON review_comments(pull_request_id_placeholder)
    WHERE is_resolved = FALSE;
