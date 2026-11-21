/*
============================================================================
REACT TESTING: UNIT TESTS, COMPONENT TESTS, MOCKING,
AND USER INTERACTION TESTING
============================================================================

PostgreSQL 15+

This script models an enterprise React testing registry and execution
workflow. It stores test suites, test cases, component specifications,
mock dependencies, user interaction scenarios, execution runs,
assertions, and test reports.

Execute:
    psql -U postgres -d postgres -f react_testing.sql

The script uses a dedicated schema and recreates it on execution.
*/

BEGIN;

DROP SCHEMA IF EXISTS react_testing CASCADE;

CREATE SCHEMA react_testing;

SET search_path TO react_testing, public;


-- =========================================================================
-- 1. ENUM TYPES
-- =========================================================================

CREATE TYPE test_category AS ENUM (
    'UNIT',
    'COMPONENT',
    'MOCKING',
    'INTERACTION',
    'INTEGRATION',
    'REGRESSION'
);

CREATE TYPE test_status AS ENUM (
    'PENDING',
    'RUNNING',
    'PASSED',
    'FAILED',
    'SKIPPED',
    'BLOCKED'
);

CREATE TYPE component_state AS ENUM (
    'IDLE',
    'LOADING',
    'SUCCESS',
    'ERROR',
    'EMPTY'
);

CREATE TYPE mock_behavior AS ENUM (
    'SUCCESS',
    'ERROR',
    'TIMEOUT',
    'EMPTY_RESPONSE',
    'MALFORMED_RESPONSE'
);

CREATE TYPE assertion_type AS ENUM (
    'EQUALS',
    'NOT_EQUALS',
    'TRUE',
    'FALSE',
    'CONTAINS',
    'ELEMENT_EXISTS',
    'ELEMENT_ABSENT',
    'CALL_COUNT',
    'STATE_EQUALS'
);


-- =========================================================================
-- 2. TEST PROJECTS
-- =========================================================================

CREATE TABLE test_projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_name VARCHAR(150) NOT NULL UNIQUE,

    application_name VARCHAR(150) NOT NULL,

    description TEXT,

    environment VARCHAR(30) NOT NULL DEFAULT 'TEST',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_environment CHECK (
        environment IN ('LOCAL', 'TEST', 'STAGING', 'CI')
    )
);


-- =========================================================================
-- 3. TEST SUITES
-- =========================================================================

CREATE TABLE test_suites (
    suite_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES test_projects(project_id),

    suite_name VARCHAR(150) NOT NULL,

    category test_category NOT NULL,

    description TEXT,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_suite_name
        UNIQUE(project_id, suite_name)
);


-- =========================================================================
-- 4. COMPONENT DEFINITIONS
-- =========================================================================

CREATE TABLE components (
    component_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES test_projects(project_id),

    component_name VARCHAR(150) NOT NULL,

    component_type VARCHAR(50) NOT NULL,

    description TEXT,

    requires_api BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_component
        UNIQUE(project_id, component_name)
);


-- =========================================================================
-- 5. TEST CASES
-- =========================================================================

CREATE TABLE test_cases (
    test_case_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    suite_id BIGINT NOT NULL
        REFERENCES test_suites(suite_id),

    component_id BIGINT
        REFERENCES components(component_id),

    test_name VARCHAR(200) NOT NULL,

    category test_category NOT NULL,

    description TEXT NOT NULL,

    expected_result TEXT NOT NULL,

    priority SMALLINT NOT NULL DEFAULT 3,

    timeout_ms INTEGER NOT NULL DEFAULT 5000,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_priority
        CHECK (priority BETWEEN 1 AND 5),

    CONSTRAINT valid_timeout
        CHECK (timeout_ms BETWEEN 1 AND 300000),

    CONSTRAINT unique_test_per_suite
        UNIQUE(suite_id, test_name)
);


-- =========================================================================
-- 6. MOCK DEPENDENCIES
-- =========================================================================

CREATE TABLE mock_dependencies (
    mock_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES test_projects(project_id),

    dependency_name VARCHAR(150) NOT NULL,

    endpoint VARCHAR(300),

    behavior mock_behavior NOT NULL,

    response_payload JSONB NOT NULL DEFAULT '{}'::JSONB,

    response_delay_ms INTEGER NOT NULL DEFAULT 0,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_response_delay
        CHECK (response_delay_ms BETWEEN 0 AND 300000),

    CONSTRAINT unique_mock
        UNIQUE(project_id, dependency_name, behavior)
);


-- =========================================================================
-- 7. TEST CASE MOCK MAPPING
-- =========================================================================

CREATE TABLE test_case_mocks (
    test_case_id BIGINT NOT NULL
        REFERENCES test_cases(test_case_id)
        ON DELETE CASCADE,

    mock_id BIGINT NOT NULL
        REFERENCES mock_dependencies(mock_id),

    required BOOLEAN NOT NULL DEFAULT TRUE,

    PRIMARY KEY(test_case_id, mock_id)
);


-- =========================================================================
-- 8. USER INTERACTION SCENARIOS
-- =========================================================================

CREATE TABLE interaction_scenarios (
    scenario_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    test_case_id BIGINT NOT NULL
        REFERENCES test_cases(test_case_id)
        ON DELETE CASCADE,

    sequence_number INTEGER NOT NULL,

    action_type VARCHAR(40) NOT NULL,

    target_element VARCHAR(150) NOT NULL,

    input_value TEXT,

    expected_state component_state,

    expected_output TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_sequence
        CHECK (sequence_number > 0),

    CONSTRAINT valid_action
        CHECK (
            action_type IN (
                'CLICK',
                'TYPE',
                'CLEAR',
                'SUBMIT',
                'SELECT',
                'HOVER',
                'KEYBOARD',
                'WAIT',
                'ASSERT'
            )
        ),

    CONSTRAINT unique_scenario_step
        UNIQUE(test_case_id, sequence_number)
);


-- =========================================================================
-- 9. ASSERTIONS
-- =========================================================================

CREATE TABLE test_assertions (
    assertion_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    test_case_id BIGINT NOT NULL
        REFERENCES test_cases(test_case_id)
        ON DELETE CASCADE,

    assertion_name VARCHAR(200) NOT NULL,

    assertion_kind assertion_type NOT NULL,

    expected_value TEXT NOT NULL,

    actual_value TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_assertion_name
        UNIQUE(test_case_id, assertion_name)
);


-- =========================================================================
-- 10. EXECUTION RUNS
-- =========================================================================

CREATE TABLE test_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES test_projects(project_id),

    run_name VARCHAR(150) NOT NULL,

    environment VARCHAR(30) NOT NULL,

    status test_status NOT NULL DEFAULT 'PENDING',

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    total_tests INTEGER NOT NULL DEFAULT 0,

    passed_tests INTEGER NOT NULL DEFAULT 0,

    failed_tests INTEGER NOT NULL DEFAULT 0,

    skipped_tests INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_run_environment
        CHECK (
            environment IN ('LOCAL', 'TEST', 'STAGING', 'CI')
        ),

    CONSTRAINT nonnegative_counts
        CHECK (
            total_tests >= 0
            AND passed_tests >= 0
            AND failed_tests >= 0
            AND skipped_tests >= 0
        ),

    CONSTRAINT valid_run_counts
        CHECK (
            passed_tests + failed_tests + skipped_tests
            <= total_tests
        ),

    CONSTRAINT valid_run_timestamps
        CHECK (
            completed_at IS NULL
            OR started_at IS NULL
            OR completed_at >= started_at
        )
);


-- =========================================================================
-- 11. TEST EXECUTION RESULTS
-- =========================================================================

CREATE TABLE test_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES test_runs(run_id)
        ON DELETE CASCADE,

    test_case_id BIGINT NOT NULL
        REFERENCES test_cases(test_case_id),

    status test_status NOT NULL,

    actual_output TEXT,

    error_message TEXT,

    execution_time_ms INTEGER NOT NULL DEFAULT 0,

    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_execution_time
        CHECK (execution_time_ms >= 0),

    CONSTRAINT unique_test_result
        UNIQUE(run_id, test_case_id),

    CONSTRAINT valid_result_error
        CHECK (
            status <> 'FAILED'
            OR error_message IS NOT NULL
        )
);


-- =========================================================================
-- 12. ASSERTION EXECUTION RESULTS
-- =========================================================================

CREATE TABLE assertion_results (
    assertion_result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    result_id BIGINT NOT NULL
        REFERENCES test_results(result_id)
        ON DELETE CASCADE,

    assertion_id BIGINT NOT NULL
        REFERENCES test_assertions(assertion_id),

    passed BOOLEAN NOT NULL,

    expected_value TEXT NOT NULL,

    actual_value TEXT NOT NULL,

    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_assertion_execution
        UNIQUE(result_id, assertion_id)
);


-- =========================================================================
-- 13. INDEXES
-- =========================================================================

CREATE INDEX idx_test_cases_suite_enabled
    ON test_cases(suite_id, priority DESC)
    WHERE enabled = TRUE;

CREATE INDEX idx_test_cases_component
    ON test_cases(component_id)
    WHERE component_id IS NOT NULL;

CREATE INDEX idx_mock_project_behavior
    ON mock_dependencies(project_id, behavior);

CREATE INDEX idx_scenarios_case_sequence
    ON interaction_scenarios(test_case_id, sequence_number);

CREATE INDEX idx_runs_project_date
    ON test_runs(project_id, created_at DESC);

CREATE INDEX idx_results_run_status
    ON test_results(run_id, status);

CREATE INDEX idx_results_failed
    ON test_results(executed_at DESC)
    WHERE status = 'FAILED';

CREATE INDEX idx_mock_payload
    ON mock_dependencies
    USING GIN(response_payload);


-- =========================================================================
-- 14. SAMPLE PROJECT
-- =========================================================================

INSERT INTO test_projects (
    project_name,
    application_name,
    description,
    environment
)
VALUES (
    'REACT_USER_DIRECTORY',
    'User Directory',
    'Testing user search, API loading, selection and error states',
    'TEST'
);


-- =========================================================================
-- 15. TEST SUITES
-- =========================================================================

INSERT INTO test_suites (
    project_id,
    suite_name,
    category,
    description
)
SELECT
    project_id,
    suite_name,
    category,
    description
FROM test_projects
CROSS JOIN (
    VALUES
    (
        'Email Validation',
        'UNIT'::test_category,
        'Pure function validation'
    ),
    (
        'User Directory Rendering',
        'COMPONENT'::test_category,
        'Component state and rendering'
    ),
    (
        'API Mocking',
        'MOCKING'::test_category,
        'Dependency isolation and simulated failures'
    ),
    (
        'User Interactions',
        'INTERACTION'::test_category,
        'Search, clear, select and empty-state behavior'
    ),
    (
        'Regression Tests',
        'REGRESSION'::test_category,
        'Previously detected behavioral failures'
    )
) AS suites(suite_name, category, description)
WHERE project_name = 'REACT_USER_DIRECTORY';


-- =========================================================================
-- 16. COMPONENT RECORDS
-- =========================================================================

INSERT INTO components (
    project_id,
    component_name,
    component_type,
    description,
    requires_api
)
SELECT
    project_id,
    component_name,
    component_type,
    description,
    requires_api
FROM test_projects
CROSS JOIN (
    VALUES
    (
        'UserDirectory',
        'FUNCTIONAL',
        'Main user listing and search component',
        TRUE
    ),
    (
        'SearchInput',
        'CONTROLLED_INPUT',
        'User-controlled search input',
        FALSE
    ),
    (
        'UserList',
        'LIST',
        'Displays filtered users',
        FALSE
    ),
    (
        'UserCard',
        'PRESENTATIONAL',
        'Displays an individual user',
        FALSE
    )
) AS c(
    component_name,
    component_type,
    description,
    requires_api
)
WHERE project_name = 'REACT_USER_DIRECTORY';


-- =========================================================================
-- 17. TEST CASE DATA
-- =========================================================================

INSERT INTO test_cases (
    suite_id,
    component_id,
    test_name,
    category,
    description,
    expected_result,
    priority
)
SELECT
    s.suite_id,
    c.component_id,
    test_data.test_name,
    test_data.category,
    test_data.description,
    test_data.expected_result,
    test_data.priority
FROM test_suites s
JOIN test_projects p
    ON p.project_id = s.project_id
LEFT JOIN components c
    ON c.project_id = p.project_id
   AND c.component_name = test_data_component.component_name
CROSS JOIN (
    VALUES
    (
        'Email Validation',
        'SearchInput',
        'Valid email',
        'UNIT'::test_category,
        'Valid email format must be accepted',
        'TRUE',
        5
    ),
    (
        'Email Validation',
        'SearchInput',
        'Malformed email',
        'UNIT'::test_category,
        'Malformed email must be rejected',
        'FALSE',
        5
    ),
    (
        'User Directory Rendering',
        'UserDirectory',
        'Initial loading state',
        'COMPONENT'::test_category,
        'Loading indicator appears before data retrieval',
        'LOADING',
        5
    ),
    (
        'User Directory Rendering',
        'UserDirectory',
        'Successful user rendering',
        'COMPONENT'::test_category,
        'Users appear after successful retrieval',
        'SUCCESS',
        5
    ),
    (
        'User Directory Rendering',
        'UserDirectory',
        'Empty API response',
        'COMPONENT'::test_category,
        'Empty result message is displayed',
        'EMPTY',
        4
    ),
    (
        'User Directory Rendering',
        'UserDirectory',
        'API error state',
        'COMPONENT'::test_category,
        'API error is displayed to the user',
        'ERROR',
        5
    ),
    (
        'API Mocking',
        'UserDirectory',
        'Successful API mock',
        'MOCKING'::test_category,
        'Mock dependency returns controlled user records',
        'SUCCESS',
        5
    ),
    (
        'API Mocking',
        'UserDirectory',
        'Failed API mock',
        'MOCKING'::test_category,
        'Mock dependency simulates network failure',
        'ERROR',
        5
    ),
    (
        'User Interactions',
        'SearchInput',
        'Search by name',
        'INTERACTION'::test_category,
        'Typing filters users by name',
        'ONE_MATCH',
        5
    ),
    (
        'User Interactions',
        'SearchInput',
        'Clear search',
        'INTERACTION'::test_category,
        'Clearing the search restores all users',
        'ALL_USERS',
        4
    ),
    (
        'User Interactions',
        'UserCard',
        'Select user',
        'INTERACTION'::test_category,
        'Selection callback receives the selected user',
        'SELECTED',
        5
    ),
    (
        'User Interactions',
        'UserList',
        'No matching users',
        'INTERACTION'::test_category,
        'No-match feedback is displayed',
        'EMPTY',
        4
    ),
    (
        'Regression Tests',
        'UserDirectory',
        'Duplicate API response protection',
        'REGRESSION'::test_category,
        'Repeated requests must not duplicate user records',
        'UNIQUE_USERS',
        3
    )
) AS test_data(
    suite_name,
    component_name,
    test_name,
    category,
    description,
    expected_result,
    priority
)
JOIN LATERAL (
    SELECT test_data.component_name
) AS test_data_component ON TRUE
WHERE s.suite_name = test_data.suite_name
  AND p.project_name = 'REACT_USER_DIRECTORY';


-- =========================================================================
-- 18. MOCK DEPENDENCIES
-- =========================================================================

INSERT INTO mock_dependencies (
    project_id,
    dependency_name,
    endpoint,
    behavior,
    response_payload,
    response_delay_ms
)
SELECT
    project_id,
    m.dependency_name,
    m.endpoint,
    m.behavior,
    m.payload::JSONB,
    m.delay_ms
FROM test_projects
CROSS JOIN (
    VALUES
    (
        'User API Success',
        '/api/users',
        'SUCCESS'::mock_behavior,
        '{"users":[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]}',
        10
    ),
    (
        'User API Failure',
        '/api/users',
        'ERROR'::mock_behavior,
        '{"message":"Network unavailable"}',
        0
    ),
    (
        'User API Timeout',
        '/api/users',
        'TIMEOUT'::mock_behavior,
        '{"message":"Request timed out"}',
        30000
    ),
    (
        'User API Empty',
        '/api/users',
        'EMPTY_RESPONSE'::mock_behavior,
        '{"users":[]}',
        5
    ),
    (
        'User API Invalid',
        '/api/users',
        'MALFORMED_RESPONSE'::mock_behavior,
        '{"users":"invalid"}',
        5
    )
) AS m(
    dependency_name,
    endpoint,
    behavior,
    payload,
    delay_ms
)
WHERE project_name = 'REACT_USER_DIRECTORY';


-- =========================================================================
-- 19. INTERACTION STEPS
-- =========================================================================

INSERT INTO interaction_scenarios (
    test_case_id,
    sequence_number,
    action_type,
    target_element,
    input_value,
    expected_state,
    expected_output
)
SELECT
    tc.test_case_id,
    steps.sequence_number,
    steps.action_type,
    steps.target_element,
    steps.input_value,
    steps.expected_state,
    steps.expected_output
FROM test_cases tc
JOIN test_suites ts
    ON ts.suite_id = tc.suite_id
JOIN test_projects p
    ON p.project_id = ts.project_id
CROSS JOIN (
    VALUES
    (
        'Search by name',
        1,
        'TYPE',
        'user-search',
        'alice',
        'SUCCESS'::component_state,
        'One matching user'
    ),
    (
        'Search by name',
        2,
        'ASSERT',
        'user-list',
        NULL,
        'SUCCESS'::component_state,
        'Alice is visible'
    ),
    (
        'Clear search',
        1,
        'CLEAR',
        'user-search',
        NULL,
        'SUCCESS'::component_state,
        'Search input is empty'
    ),
    (
        'Clear search',
        2,
        'ASSERT',
        'user-list',
        NULL,
        'SUCCESS'::component_state,
        'All users are visible'
    ),
    (
        'Select user',
        1,
        'CLICK',
        'select-user-1',
        NULL,
        'SUCCESS'::component_state,
        'Selection callback invoked'
    ),
    (
        'No matching users',
        1,
        'TYPE',
        'user-search',
        'unknown-user',
        'SUCCESS'::component_state,
        'No users found'
    )
) AS steps(
    test_name,
    sequence_number,
    action_type,
    target_element,
    input_value,
    expected_state,
    expected_output
)
WHERE tc.test_name = steps.test_name
  AND p.project_name = 'REACT_USER_DIRECTORY';


-- =========================================================================
-- 20. ASSERTION DEFINITIONS
-- =========================================================================

INSERT INTO test_assertions (
    test_case_id,
    assertion_name,
    assertion_kind,
    expected_value
)
SELECT
    tc.test_case_id,
    a.assertion_name,
    a.assertion_kind,
    a.expected_value
FROM test_cases tc
JOIN test_suites ts
    ON ts.suite_id = tc.suite_id
JOIN test_projects p
    ON p.project_id = ts.project_id
CROSS JOIN (
    VALUES
    (
        'Valid email',
        'Email accepted',
        'TRUE'::assertion_type,
        'true'
    ),
    (
        'Malformed email',
        'Email rejected',
        'FALSE'::assertion_type,
        'false'
    ),
    (
        'Successful user rendering',
        'Users visible',
        'ELEMENT_EXISTS'::assertion_type,
        'user-list'
    ),
    (
        'API error state',
        'Error displayed',
        'STATE_EQUALS'::assertion_type,
        'ERROR'
    ),
    (
        'Search by name',
        'Single search result',
        'EQUALS'::assertion_type,
        '1'
    ),
    (
        'Clear search',
        'All users restored',
        'EQUALS'::assertion_type,
        '3'
    ),
    (
        'Select user',
        'Callback count',
        'CALL_COUNT'::assertion_type,
        '1'
    ),
    (
        'No matching users',
        'Empty feedback',
        'CONTAINS'::assertion_type,
        'No users found'
    )
) AS a(
    test_name,
    assertion_name,
    assertion_kind,
    expected_value
)
WHERE tc.test_name = a.test_name
  AND p.project_name = 'REACT_USER_DIRECTORY';


-- =========================================================================
-- 21. LINK TEST CASES TO MOCK DEPENDENCIES
-- =========================================================================

INSERT INTO test_case_mocks (
    test_case_id,
    mock_id,
    required
)
SELECT
    tc.test_case_id,
    md.mock_id,
    TRUE
FROM test_cases tc
JOIN test_suites ts
    ON ts.suite_id = tc.suite_id
JOIN test_projects p
    ON p.project_id = ts.project_id
JOIN mock_dependencies md
    ON md.project_id = p.project_id
WHERE p.project_name = 'REACT_USER_DIRECTORY'
  AND (
      (tc.test_name IN (
          'Successful user rendering',
          'Successful API mock'
      ) AND md.behavior = 'SUCCESS')
      OR
      (tc.test_name IN (
          'API error state',
          'Failed API mock'
      ) AND md.behavior = 'ERROR')
      OR
      (tc.test_name = 'Empty API response'
       AND md.behavior = 'EMPTY_RESPONSE')
  );


-- =========================================================================
-- 22. TEST EXECUTION FUNCTION
-- =========================================================================

CREATE OR REPLACE FUNCTION start_test_run(
    p_project_id BIGINT,
    p_run_name VARCHAR,
    p_environment VARCHAR
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_run_id BIGINT;
BEGIN
    IF p_run_name IS NULL OR LENGTH(TRIM(p_run_name)) = 0 THEN
        RAISE EXCEPTION 'Run name is required';
    END IF;

    IF p_environment NOT IN (
        'LOCAL',
        'TEST',
        'STAGING',
        'CI'
    ) THEN
        RAISE EXCEPTION 'Invalid test environment';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM test_projects
        WHERE project_id = p_project_id
    ) THEN
        RAISE EXCEPTION 'Project does not exist';
    END IF;

    INSERT INTO test_runs (
        project_id,
        run_name,
        environment,
        status,
        started_at
    )
    VALUES (
        p_project_id,
        p_run_name,
        p_environment,
        'RUNNING',
        NOW()
    )
    RETURNING run_id INTO v_run_id;

    RETURN v_run_id;
END;
$$;


-- =========================================================================
-- 23. RECORD TEST RESULT FUNCTION
-- =========================================================================

CREATE OR REPLACE FUNCTION record_test_result(
    p_run_id BIGINT,
    p_test_case_id BIGINT,
    p_status test_status,
    p_actual_output TEXT,
    p_error_message TEXT,
    p_execution_time_ms INTEGER
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_result_id BIGINT;
    v_run_status test_status;
BEGIN
    IF p_status NOT IN (
        'PASSED',
        'FAILED',
        'SKIPPED',
        'BLOCKED'
    ) THEN
        RAISE EXCEPTION 'Invalid terminal test status';
    END IF;

    IF p_execution_time_ms < 0 THEN
        RAISE EXCEPTION 'Execution time cannot be negative';
    END IF;

    SELECT status
    INTO v_run_status
    FROM test_runs
    WHERE run_id = p_run_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Test run does not exist';
    END IF;

    IF v_run_status <> 'RUNNING' THEN
        RAISE EXCEPTION 'Test run is not accepting results';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM test_cases tc
        JOIN test_suites ts
            ON ts.suite_id = tc.suite_id
        JOIN test_runs tr
            ON tr.project_id = ts.project_id
        WHERE tr.run_id = p_run_id
          AND tc.test_case_id = p_test_case_id
          AND tc.enabled = TRUE
          AND ts.enabled = TRUE
    ) THEN
        RAISE EXCEPTION
            'Test case is disabled or belongs to another project';
    END IF;

    IF p_status = 'FAILED'
       AND p_error_message IS NULL THEN
        RAISE EXCEPTION
            'Failed tests require an error message';
    END IF;

    INSERT INTO test_results (
        run_id,
        test_case_id,
        status,
        actual_output,
        error_message,
        execution_time_ms
    )
    VALUES (
        p_run_id,
        p_test_case_id,
        p_status,
        p_actual_output,
        p_error_message,
        p_execution_time_ms
    )
    RETURNING result_id INTO v_result_id;

    UPDATE test_runs
    SET
        total_tests = total_tests + 1,
        passed_tests = passed_tests +
            CASE WHEN p_status = 'PASSED' THEN 1 ELSE 0 END,
        failed_tests = failed_tests +
            CASE WHEN p_status = 'FAILED' THEN 1 ELSE 0 END,
        skipped_tests = skipped_tests +
            CASE WHEN p_status IN ('SKIPPED', 'BLOCKED') THEN 1 ELSE 0 END
    WHERE run_id = p_run_id;

    RETURN v_result_id;
END;
$$;


-- =========================================================================
-- 24. COMPLETE TEST RUN FUNCTION
-- =========================================================================

CREATE OR REPLACE FUNCTION complete_test_run(
    p_run_id BIGINT
)
RETURNS test_status
LANGUAGE plpgsql
AS $$
DECLARE
    v_run test_runs%ROWTYPE;
    v_expected INTEGER;
    v_status test_status;
BEGIN
    SELECT *
    INTO v_run
    FROM test_runs
    WHERE run_id = p_run_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Test run not found';
    END IF;

    IF v_run.status <> 'RUNNING' THEN
        RAISE EXCEPTION 'Test run is not running';
    END IF;

    SELECT COUNT(*)
    INTO v_expected
    FROM test_cases tc
    JOIN test_suites ts
        ON ts.suite_id = tc.suite_id
    WHERE ts.project_id = v_run.project_id
      AND ts.enabled = TRUE
      AND tc.enabled = TRUE;

    IF v_run.total_tests = 0 THEN
        v_status := 'BLOCKED';

    ELSIF v_run.total_tests < v_expected THEN
        v_status := 'BLOCKED';

    ELSIF v_run.failed_tests > 0 THEN
        v_status := 'FAILED';

    ELSE
        v_status := 'PASSED';
    END IF;

    UPDATE test_runs
    SET
        status = v_status,
        completed_at = NOW()
    WHERE run_id = p_run_id;

    RETURN v_status;
END;
$$;


-- =========================================================================
-- 25. VALIDATION VIEW
-- =========================================================================

CREATE OR REPLACE VIEW test_case_readiness AS
SELECT
    tc.test_case_id,
    p.project_name,
    ts.suite_name,
    tc.test_name,
    tc.category,
    tc.priority,
    tc.enabled,
    COALESCE(m.mock_count, 0) AS mock_count,
    COALESCE(a.assertion_count, 0) AS assertion_count,
    COALESCE(i.interaction_count, 0) AS interaction_count,

    CASE
        WHEN NOT tc.enabled THEN 'DISABLED'

        WHEN tc.category = 'MOCKING'
             AND COALESCE(m.mock_count, 0) = 0
            THEN 'MISSING_MOCK'

        WHEN tc.category = 'INTERACTION'
             AND COALESCE(i.interaction_count, 0) = 0
            THEN 'MISSING_INTERACTION'

        WHEN COALESCE(a.assertion_count, 0) = 0
            THEN 'MISSING_ASSERTION'

        ELSE 'READY'
    END AS readiness_status

FROM test_cases tc

JOIN test_suites ts
    ON ts.suite_id = tc.suite_id

JOIN test_projects p
    ON p.project_id = ts.project_id

LEFT JOIN (
    SELECT
        test_case_id,
        COUNT(*) AS mock_count
    FROM test_case_mocks
    GROUP BY test_case_id
) m ON m.test_case_id = tc.test_case_id

LEFT JOIN (
    SELECT
        test_case_id,
        COUNT(*) AS assertion_count
    FROM test_assertions
    GROUP BY test_case_id
) a ON a.test_case_id = tc.test_case_id

LEFT JOIN (
    SELECT
        test_case_id,
        COUNT(*) AS interaction_count
    FROM interaction_scenarios
    GROUP BY test_case_id
) i ON i.test_case_id = tc.test_case_id;


-- =========================================================================
-- 26. TEST EXECUTION REPORT VIEW
-- =========================================================================

CREATE OR REPLACE VIEW test_execution_report AS
SELECT
    tr.run_id,
    p.project_name,
    tr.run_name,
    tr.environment,
    tr.status,
    tr.total_tests,
    tr.passed_tests,
    tr.failed_tests,
    tr.skipped_tests,

    ROUND(
        100.0 * tr.passed_tests /
        NULLIF(tr.total_tests, 0),
        2
    ) AS pass_percentage,

    ROUND(
        COALESCE(
            AVG(result.execution_time_ms),
            0
        ),
        2
    ) AS average_execution_ms,

    tr.started_at,
    tr.completed_at

FROM test_runs tr

JOIN test_projects p
    ON p.project_id = tr.project_id

LEFT JOIN test_results result
    ON result.run_id = tr.run_id

GROUP BY
    tr.run_id,
    p.project_name,
    tr.run_name,
    tr.environment,
    tr.status,
    tr.total_tests,
    tr.passed_tests,
    tr.failed_tests,
    tr.skipped_tests,
    tr.started_at,
    tr.completed_at;


-- =========================================================================
-- 27. FAILURE ANALYSIS VIEW
-- =========================================================================

CREATE OR REPLACE VIEW failed_test_analysis AS
SELECT
    p.project_name,
    tr.run_name,
    tc.test_name,
    tc.category,
    tc.priority,
    result.error_message,
    result.actual_output,
    result.execution_time_ms,
    result.executed_at

FROM test_results result

JOIN test_runs tr
    ON tr.run_id = result.run_id

JOIN test_cases tc
    ON tc.test_case_id = result.test_case_id

JOIN test_projects p
    ON p.project_id = tr.project_id

WHERE result.status = 'FAILED';


-- =========================================================================
-- 28. WORKFLOW: CREATE EXECUTION RUN
-- =========================================================================

DO $$
DECLARE
    v_project_id BIGINT;
    v_run_id BIGINT;
    v_case_id BIGINT;
    v_status test_status;
BEGIN
    SELECT project_id
    INTO v_project_id
    FROM test_projects
    WHERE project_name = 'REACT_USER_DIRECTORY';

    v_run_id := start_test_run(
        v_project_id,
        'Initial React Testing Execution',
        'TEST'
    );

    -- Record successful pure-function tests.
    SELECT test_case_id
    INTO v_case_id
    FROM test_cases
    WHERE test_name = 'Valid email';

    PERFORM record_test_result(
        v_run_id,
        v_case_id,
        'PASSED',
        'true',
        NULL,
        2
    );

    SELECT test_case_id
    INTO v_case_id
    FROM test_cases
    WHERE test_name = 'Malformed email';

    PERFORM record_test_result(
        v_run_id,
        v_case_id,
        'PASSED',
        'false',
        NULL,
        1
    );

    -- Record successful component rendering.
    SELECT test_case_id
    INTO v_case_id
    FROM test_cases
    WHERE test_name = 'Successful user rendering';

    PERFORM record_test_result(
        v_run_id,
        v_case_id,
        'PASSED',
        'User list rendered',
        NULL,
        15
    );

    -- Record a realistic failed API interaction.
    SELECT test_case_id
    INTO v_case_id
    FROM test_cases
    WHERE test_name = 'API error state';

    PERFORM record_test_result(
        v_run_id,
        v_case_id,
        'FAILED',
        'Unexpected loading state',
        'Error state was not rendered',
        5000
    );

    -- Complete the run. Missing test executions produce BLOCKED.
    v_status := complete_test_run(v_run_id);

    RAISE NOTICE 'Execution run % completed with status %',
        v_run_id,
        v_status;
END;
$$;


-- =========================================================================
-- 29. RETRIEVAL QUERIES
-- =========================================================================

-- All registered suites.
SELECT
    suite_id,
    suite_name,
    category,
    enabled
FROM test_suites
ORDER BY suite_id;


-- All test cases by priority.
SELECT
    tc.test_name,
    tc.category,
    tc.priority,
    ts.suite_name
FROM test_cases tc
JOIN test_suites ts
    ON ts.suite_id = tc.suite_id
ORDER BY tc.priority DESC, tc.test_name;


-- Component-level test inventory.
SELECT
    c.component_name,
    COUNT(tc.test_case_id) AS test_count
FROM components c
LEFT JOIN test_cases tc
    ON tc.component_id = c.component_id
GROUP BY c.component_id, c.component_name
ORDER BY test_count DESC;


-- =========================================================================
-- 30. TEST READINESS EVALUATION
-- =========================================================================

SELECT
    test_case_id,
    suite_name,
    test_name,
    category,
    readiness_status
FROM test_case_readiness
ORDER BY
    CASE readiness_status
        WHEN 'READY' THEN 1
        WHEN 'MISSING_ASSERTION' THEN 2
        WHEN 'MISSING_MOCK' THEN 3
        WHEN 'MISSING_INTERACTION' THEN 4
        ELSE 5
    END,
    priority DESC;


-- =========================================================================
-- 31. MOCKING REPORT
-- =========================================================================

SELECT
    dependency_name,
    endpoint,
    behavior,
    response_delay_ms,
    response_payload
FROM mock_dependencies
ORDER BY dependency_name;


-- =========================================================================
-- 32. USER INTERACTION REPORT
-- =========================================================================

SELECT
    tc.test_name,
    scenario.sequence_number,
    scenario.action_type,
    scenario.target_element,
    scenario.input_value,
    scenario.expected_state,
    scenario.expected_output
FROM interaction_scenarios scenario
JOIN test_cases tc
    ON tc.test_case_id = scenario.test_case_id
ORDER BY tc.test_name, scenario.sequence_number;


-- =========================================================================
-- 33. EXECUTION AGGREGATION
-- =========================================================================

SELECT
    project_name,
    run_name,
    status,
    total_tests,
    passed_tests,
    failed_tests,
    skipped_tests,
    pass_percentage,
    average_execution_ms
FROM test_execution_report
ORDER BY run_id DESC;


-- =========================================================================
-- 34. FAILURE ANALYSIS
-- =========================================================================

SELECT
    test_name,
    category,
    error_message,
    execution_time_ms,
    executed_at
FROM failed_test_analysis
ORDER BY executed_at DESC;


-- =========================================================================
-- 35. CATEGORY-LEVEL QUALITY REPORT
-- =========================================================================

SELECT
    tc.category,

    COUNT(DISTINCT tc.test_case_id) AS registered_tests,

    COUNT(result.result_id) AS executed_tests,

    COUNT(*) FILTER (
        WHERE result.status = 'PASSED'
    ) AS passed_tests,

    COUNT(*) FILTER (
        WHERE result.status = 'FAILED'
    ) AS failed_tests,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE result.status = 'PASSED'
        ) / NULLIF(COUNT(result.result_id), 0),
        2
    ) AS pass_percentage

FROM test_cases tc

JOIN test_suites ts
    ON ts.suite_id = tc.suite_id

LEFT JOIN test_results result
    ON result.test_case_id = tc.test_case_id

GROUP BY tc.category
ORDER BY tc.category;


-- =========================================================================
-- 36. ELIGIBILITY DETERMINATION
-- =========================================================================

-- A test suite is eligible for execution only when it is enabled
-- and all enabled test cases satisfy their readiness conditions.

SELECT
    ts.suite_name,

    COUNT(readiness.test_case_id) AS total_cases,

    COUNT(*) FILTER (
        WHERE readiness.readiness_status = 'READY'
    ) AS ready_cases,

    CASE
        WHEN NOT ts.enabled THEN 'INELIGIBLE'

        WHEN COUNT(readiness.test_case_id) = 0
            THEN 'INELIGIBLE'

        WHEN COUNT(*) FILTER (
            WHERE readiness.readiness_status <> 'READY'
        ) > 0
            THEN 'INELIGIBLE'

        ELSE 'ELIGIBLE'
    END AS execution_eligibility

FROM test_suites ts

LEFT JOIN test_case_readiness readiness
    ON readiness.suite_name = ts.suite_name

GROUP BY ts.suite_id, ts.suite_name, ts.enabled
ORDER BY ts.suite_name;


-- =========================================================================
-- 37. TRANSACTION AND INTEGRITY DEMONSTRATION
-- =========================================================================

-- The following transaction illustrates atomic execution-result
-- recording. A duplicate result violates the unique constraint.
-- The transaction is rolled back to preserve the existing report.

SAVEPOINT before_integrity_test;

DO $$
DECLARE
    v_run_id BIGINT;
    v_case_id BIGINT;
BEGIN
    SELECT run_id
    INTO v_run_id
    FROM test_runs
    WHERE run_name = 'Initial React Testing Execution';

    SELECT test_case_id
    INTO v_case_id
    FROM test_cases
    WHERE test_name = 'Valid email';

    BEGIN
        INSERT INTO test_results (
            run_id,
            test_case_id,
            status,
            actual_output,
            execution_time_ms
        )
        VALUES (
            v_run_id,
            v_case_id,
            'PASSED',
            'Duplicate result',
            1
        );

    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE
                'Duplicate test result rejected by database constraint';
    END;
END;
$$;

ROLLBACK TO SAVEPOINT before_integrity_test;

RELEASE SAVEPOINT before_integrity_test;


-- =========================================================================
-- 38. FINAL DATABASE VALIDATION
-- =========================================================================

DO $$
DECLARE
    v_projects INTEGER;
    v_suites INTEGER;
    v_cases INTEGER;
    v_mocks INTEGER;
    v_runs INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_projects FROM test_projects;
    SELECT COUNT(*) INTO v_suites FROM test_suites;
    SELECT COUNT(*) INTO v_cases FROM test_cases;
    SELECT COUNT(*) INTO v_mocks FROM mock_dependencies;
    SELECT COUNT(*) INTO v_runs FROM test_runs;

    RAISE NOTICE 'React Testing database validation';
    RAISE NOTICE 'Projects: %', v_projects;
    RAISE NOTICE 'Suites: %', v_suites;
    RAISE NOTICE 'Test cases: %', v_cases;
    RAISE NOTICE 'Mock dependencies: %', v_mocks;
    RAISE NOTICE 'Execution runs: %', v_runs;

    IF v_projects <> 1 OR v_suites <> 5 OR v_cases <> 13 THEN
        RAISE EXCEPTION
            'Unexpected database initialization counts';
    END IF;
END;
$$;

COMMIT;
