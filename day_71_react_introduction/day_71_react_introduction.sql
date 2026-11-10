-- =========================================================
-- REACT INTRODUCTION
-- COMPONENT ARCHITECTURE, JSX, VIRTUAL DOM AND RENDERING
-- PostgreSQL 14+
-- =========================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS react_learning;

SET search_path TO react_learning, public;

-- =========================================================
-- 1. ENUM TYPES
-- =========================================================

CREATE TYPE component_category AS ENUM (
    'APPLICATION',
    'LAYOUT',
    'CONTENT',
    'INTERACTIVE',
    'UTILITY'
);

CREATE TYPE node_type AS ENUM (
    'ELEMENT',
    'TEXT',
    'FRAGMENT'
);

CREATE TYPE render_status AS ENUM (
    'PENDING',
    'RENDERED',
    'FAILED',
    'SUPERSEDED'
);

CREATE TYPE component_status AS ENUM (
    'ACTIVE',
    'DEPRECATED',
    'DISABLED'
);

-- =========================================================
-- 2. APPLICATIONS
-- =========================================================

CREATE TABLE applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_name VARCHAR(120) NOT NULL UNIQUE,

    description TEXT NOT NULL,

    entry_component_id BIGINT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (length(trim(application_name)) > 0)
);

-- =========================================================
-- 3. COMPONENT REGISTRY
-- =========================================================

CREATE TABLE components (
    component_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    component_name VARCHAR(120) NOT NULL,

    category component_category NOT NULL,

    component_version INTEGER NOT NULL DEFAULT 1,

    status component_status NOT NULL DEFAULT 'ACTIVE',

    description TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (
        application_id,
        component_name,
        component_version
    ),

    UNIQUE (application_id, component_id),

    CHECK (component_version > 0),

    CHECK (length(trim(component_name)) > 0)
);

ALTER TABLE applications
ADD CONSTRAINT fk_application_entry_component
FOREIGN KEY (application_id, entry_component_id)
REFERENCES components(application_id, component_id)
DEFERRABLE INITIALLY DEFERRED;

-- =========================================================
-- 4. COMPONENT PROPERTIES
-- =========================================================

CREATE TABLE component_props (
    prop_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    prop_name VARCHAR(120) NOT NULL,

    data_type VARCHAR(30) NOT NULL,

    is_required BOOLEAN NOT NULL DEFAULT FALSE,

    default_value JSONB,

    UNIQUE (component_id, prop_name),

    CHECK (
        data_type IN (
            'STRING',
            'NUMBER',
            'BOOLEAN',
            'OBJECT',
            'ARRAY'
        )
    ),

    CHECK (length(trim(prop_name)) > 0)
);

-- =========================================================
-- 5. VIRTUAL DOM TREES
-- =========================================================

CREATE TABLE virtual_dom_trees (
    tree_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    tree_version INTEGER NOT NULL,

    root_node_id BIGINT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (application_id, tree_version),

    CHECK (tree_version > 0)
);

-- =========================================================
-- 6. VIRTUAL DOM NODES
-- =========================================================

CREATE TABLE virtual_dom_nodes (
    node_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    tree_id BIGINT NOT NULL
        REFERENCES virtual_dom_trees(tree_id)
        ON DELETE CASCADE,

    parent_node_id BIGINT,

    component_id BIGINT
        REFERENCES components(component_id)
        ON DELETE SET NULL,

    node_kind node_type NOT NULL,

    element_tag VARCHAR(80),

    text_content TEXT,

    child_position INTEGER NOT NULL DEFAULT 0,

    props JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (tree_id, node_id),

    FOREIGN KEY (tree_id, parent_node_id)
        REFERENCES virtual_dom_nodes(tree_id, node_id)
        DEFERRABLE INITIALLY DEFERRED,

    CHECK (child_position >= 0),

    CHECK (jsonb_typeof(props) = 'object'),

    CHECK (
        (
            node_kind = 'ELEMENT'
            AND element_tag IS NOT NULL
            AND text_content IS NULL
        )
        OR
        (
            node_kind = 'TEXT'
            AND element_tag IS NULL
            AND text_content IS NOT NULL
            AND component_id IS NULL
        )
        OR
        (
            node_kind = 'FRAGMENT'
            AND element_tag IS NULL
            AND text_content IS NULL
        )
    )
);

ALTER TABLE virtual_dom_trees
ADD CONSTRAINT fk_tree_root_node
FOREIGN KEY (tree_id, root_node_id)
REFERENCES virtual_dom_nodes(tree_id, node_id)
DEFERRABLE INITIALLY DEFERRED;

CREATE UNIQUE INDEX idx_tree_root_unique
ON virtual_dom_nodes(tree_id)
WHERE parent_node_id IS NULL;

CREATE UNIQUE INDEX idx_tree_sibling_position
ON virtual_dom_nodes(tree_id, parent_node_id, child_position)
WHERE parent_node_id IS NOT NULL;

CREATE INDEX idx_nodes_component
ON virtual_dom_nodes(component_id)
WHERE component_id IS NOT NULL;

-- =========================================================
-- 7. COMPONENT DEPENDENCIES
-- =========================================================

CREATE TABLE component_dependencies (
    parent_component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    child_component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    dependency_type VARCHAR(30) NOT NULL DEFAULT 'COMPOSITION',

    PRIMARY KEY (
        parent_component_id,
        child_component_id
    ),

    CHECK (
        dependency_type IN (
            'COMPOSITION',
            'LAYOUT',
            'CONDITIONAL'
        )
    ),

    CHECK (parent_component_id <> child_component_id)
);

-- =========================================================
-- 8. COMPONENT STATE
-- =========================================================

CREATE TABLE component_state (
    state_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    state_key VARCHAR(120) NOT NULL,

    state_value JSONB NOT NULL,

    state_version BIGINT NOT NULL DEFAULT 1,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (component_id, state_key),

    CHECK (state_version > 0)
);

-- =========================================================
-- 9. RENDER OPERATIONS
-- =========================================================

CREATE TABLE render_operations (
    render_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    tree_id BIGINT
        REFERENCES virtual_dom_trees(tree_id)
        ON DELETE SET NULL,

    render_status render_status NOT NULL DEFAULT 'PENDING',

    render_duration_ms NUMERIC(12, 3),

    error_message TEXT,

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    completed_at TIMESTAMPTZ,

    CHECK (
        render_duration_ms IS NULL
        OR render_duration_ms >= 0
    ),

    CHECK (
        (render_status = 'FAILED' AND error_message IS NOT NULL)
        OR
        (render_status <> 'FAILED')
    ),

    CHECK (
        completed_at IS NULL
        OR completed_at >= started_at
    )
);

CREATE INDEX idx_render_application_status
ON render_operations(
    application_id,
    render_status,
    started_at DESC
);

-- =========================================================
-- 10. VIRTUAL DOM PATCHES
-- =========================================================

CREATE TABLE dom_patches (
    patch_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    render_id BIGINT NOT NULL
        REFERENCES render_operations(render_id)
        ON DELETE CASCADE,

    patch_type VARCHAR(30) NOT NULL,

    node_path VARCHAR(500) NOT NULL,

    old_value JSONB,

    new_value JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (
        patch_type IN (
            'INSERT',
            'REMOVE',
            'REPLACE',
            'UPDATE_TEXT',
            'UPDATE_PROPS'
        )
    )
);

CREATE INDEX idx_patches_render
ON dom_patches(render_id, patch_id);

-- =========================================================
-- 11. DATA INTEGRITY TRIGGERS
-- =========================================================

CREATE OR REPLACE FUNCTION validate_virtual_node()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.node_kind = 'ELEMENT' THEN
        IF NEW.element_tag !~ '^[A-Za-z][A-Za-z0-9-]*$' THEN
            RAISE EXCEPTION
                'Invalid element tag: %',
                NEW.element_tag;
        END IF;
    END IF;

    IF NEW.node_kind = 'TEXT' AND NEW.text_content IS NULL THEN
        RAISE EXCEPTION
            'Text nodes require text content.';
    END IF;

    IF NEW.parent_node_id = NEW.node_id THEN
        RAISE EXCEPTION
            'A node cannot be its own parent.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_virtual_node
BEFORE INSERT OR UPDATE
ON virtual_dom_nodes
FOR EACH ROW
EXECUTE FUNCTION validate_virtual_node();


CREATE OR REPLACE FUNCTION update_component_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_component_updated_at
BEFORE UPDATE
ON components
FOR EACH ROW
EXECUTE FUNCTION update_component_timestamp();


-- =========================================================
-- 12. STATE UPDATE FUNCTION
-- Optimistic concurrency through expected version.
-- =========================================================

CREATE OR REPLACE FUNCTION update_component_state(
    p_component_id BIGINT,
    p_state_key VARCHAR,
    p_new_value JSONB,
    p_expected_version BIGINT
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_new_version BIGINT;
BEGIN
    UPDATE component_state
    SET
        state_value = p_new_value,
        state_version = state_version + 1,
        updated_at = NOW()
    WHERE component_id = p_component_id
      AND state_key = p_state_key
      AND state_version = p_expected_version
    RETURNING state_version INTO v_new_version;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'State update conflict for component %, key %',
            p_component_id,
            p_state_key;
    END IF;

    RETURN v_new_version;
END;
$$;


-- =========================================================
-- 13. RENDER COMPLETION PROCEDURE
-- =========================================================

CREATE OR REPLACE PROCEDURE complete_render(
    p_render_id BIGINT,
    p_duration_ms NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_duration_ms < 0 THEN
        RAISE EXCEPTION
            'Render duration cannot be negative.';
    END IF;

    UPDATE render_operations
    SET
        render_status = 'RENDERED',
        render_duration_ms = p_duration_ms,
        completed_at = NOW(),
        error_message = NULL
    WHERE render_id = p_render_id
      AND render_status = 'PENDING';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Render does not exist or is not pending: %',
            p_render_id;
    END IF;
END;
$$;


-- =========================================================
-- 14. COMPONENT DEPENDENCY VIEW
-- =========================================================

CREATE OR REPLACE VIEW component_catalog AS
SELECT
    c.component_id,
    a.application_name,
    c.component_name,
    c.category,
    c.component_version,
    c.status,
    COUNT(DISTINCT d.child_component_id) AS dependency_count
FROM components c
JOIN applications a
    ON a.application_id = c.application_id
LEFT JOIN component_dependencies d
    ON d.parent_component_id = c.component_id
GROUP BY
    c.component_id,
    a.application_name,
    c.component_name,
    c.category,
    c.component_version,
    c.status;


-- =========================================================
-- 15. RENDER PERFORMANCE VIEW
-- =========================================================

CREATE OR REPLACE VIEW render_performance AS
SELECT
    a.application_name,
    COUNT(r.render_id) AS total_renders,

    COUNT(*) FILTER (
        WHERE r.render_status = 'RENDERED'
    ) AS successful_renders,

    COUNT(*) FILTER (
        WHERE r.render_status = 'FAILED'
    ) AS failed_renders,

    ROUND(
        AVG(r.render_duration_ms),
        3
    ) AS average_render_duration_ms,

    MAX(r.render_duration_ms) AS maximum_render_duration_ms

FROM applications a
LEFT JOIN render_operations r
    ON r.application_id = a.application_id
GROUP BY
    a.application_id,
    a.application_name;


-- =========================================================
-- 16. SAMPLE APPLICATION
-- =========================================================

INSERT INTO applications (
    application_name,
    description
)
VALUES (
    'React Learning Dashboard',
    'Component-based learning application demonstrating React concepts.'
);

INSERT INTO components (
    application_id,
    component_name,
    category,
    description
)
SELECT
    application_id,
    'App',
    'APPLICATION',
    'Root application component.'
FROM applications
WHERE application_name = 'React Learning Dashboard';

INSERT INTO components (
    application_id,
    component_name,
    category,
    description
)
SELECT
    application_id,
    'Header',
    'LAYOUT',
    'Displays application title and subtitle.'
FROM applications
WHERE application_name = 'React Learning Dashboard';

INSERT INTO components (
    application_id,
    component_name,
    category,
    description
)
SELECT
    application_id,
    'ConceptCard',
    'CONTENT',
    'Displays an individual React concept.'
FROM applications
WHERE application_name = 'React Learning Dashboard';

INSERT INTO components (
    application_id,
    component_name,
    category,
    description
)
SELECT
    application_id,
    'Counter',
    'INTERACTIVE',
    'Maintains and displays counter state.'
FROM applications
WHERE application_name = 'React Learning Dashboard';

INSERT INTO components (
    application_id,
    component_name,
    category,
    description
)
SELECT
    application_id,
    'ConceptList',
    'CONTENT',
    'Composes multiple concept cards.'
FROM applications
WHERE application_name = 'React Learning Dashboard';


-- =========================================================
-- 17. COMPONENT PROPERTIES
-- =========================================================

INSERT INTO component_props (
    component_id,
    prop_name,
    data_type,
    is_required
)
SELECT
    component_id,
    'title',
    'STRING',
    TRUE
FROM components
WHERE component_name = 'Header';

INSERT INTO component_props (
    component_id,
    prop_name,
    data_type,
    is_required
)
SELECT
    component_id,
    'description',
    'STRING',
    TRUE
FROM components
WHERE component_name = 'ConceptCard';

INSERT INTO component_props (
    component_id,
    prop_name,
    data_type,
    is_required
)
SELECT
    component_id,
    'count',
    'NUMBER',
    TRUE
FROM components
WHERE component_name = 'Counter';


-- =========================================================
-- 18. COMPONENT DEPENDENCIES
-- =========================================================

INSERT INTO component_dependencies (
    parent_component_id,
    child_component_id,
    dependency_type
)
SELECT
    parent.component_id,
    child.component_id,
    'COMPOSITION'
FROM components parent
JOIN components child
    ON child.application_id = parent.application_id
WHERE parent.component_name = 'App'
  AND child.component_name IN ('Header', 'ConceptList', 'Counter');

INSERT INTO component_dependencies (
    parent_component_id,
    child_component_id,
    dependency_type
)
SELECT
    parent.component_id,
    child.component_id,
    'COMPOSITION'
FROM components parent
JOIN components child
    ON child.application_id = parent.application_id
WHERE parent.component_name = 'ConceptList'
  AND child.component_name = 'ConceptCard';


-- =========================================================
-- 19. APPLICATION ENTRY COMPONENT
-- =========================================================

UPDATE applications a
SET entry_component_id = c.component_id
FROM components c
WHERE c.application_id = a.application_id
  AND c.component_name = 'App';


-- =========================================================
-- 20. INITIAL COMPONENT STATE
-- =========================================================

INSERT INTO component_state (
    component_id,
    state_key,
    state_value
)
SELECT
    component_id,
    'count',
    '0'::JSONB
FROM components
WHERE component_name = 'Counter';


-- =========================================================
-- 21. CREATE INITIAL VIRTUAL DOM TREE
-- =========================================================

INSERT INTO virtual_dom_trees (
    application_id,
    tree_version
)
SELECT application_id, 1
FROM applications
WHERE application_name = 'React Learning Dashboard';

-- Root element

INSERT INTO virtual_dom_nodes (
    tree_id,
    node_kind,
    element_tag,
    child_position,
    component_id
)
SELECT
    t.tree_id,
    'ELEMENT',
    'main',
    0,
    c.component_id
FROM virtual_dom_trees t
JOIN applications a
    ON a.application_id = t.application_id
JOIN components c
    ON c.application_id = a.application_id
WHERE t.tree_version = 1
  AND a.application_name = 'React Learning Dashboard'
  AND c.component_name = 'App';

-- Header node

INSERT INTO virtual_dom_nodes (
    tree_id,
    parent_node_id,
    node_kind,
    element_tag,
    child_position,
    props,
    component_id
)
SELECT
    root.tree_id,
    root.node_id,
    'ELEMENT',
    'header',
    0,
    '{"class": "application-header"}'::JSONB,
    c.component_id
FROM virtual_dom_nodes root
JOIN components c
    ON c.component_name = 'Header'
JOIN applications a
    ON a.application_id = c.application_id
JOIN virtual_dom_trees t
    ON t.application_id = a.application_id
   AND t.tree_id = root.tree_id
WHERE root.parent_node_id IS NULL
  AND a.application_name = 'React Learning Dashboard';

-- Header text

INSERT INTO virtual_dom_nodes (
    tree_id,
    parent_node_id,
    node_kind,
    element_tag,
    child_position,
    text_content
)
SELECT
    header.tree_id,
    header.node_id,
    'TEXT',
    NULL,
    0,
    'React Introduction'
FROM virtual_dom_nodes header
WHERE header.element_tag = 'header';

-- Concept list container

INSERT INTO virtual_dom_nodes (
    tree_id,
    parent_node_id,
    node_kind,
    element_tag,
    child_position,
    props,
    component_id
)
SELECT
    root.tree_id,
    root.node_id,
    'ELEMENT',
    'section',
    1,
    '{"class": "concept-list"}'::JSONB,
    c.component_id
FROM virtual_dom_nodes root
JOIN components c
    ON c.component_name = 'ConceptList'
WHERE root.parent_node_id IS NULL;

-- Concept cards

INSERT INTO virtual_dom_nodes (
    tree_id,
    parent_node_id,
    node_kind,
    element_tag,
    child_position,
    props,
    component_id
)
SELECT
    section.tree_id,
    section.node_id,
    'ELEMENT',
    'article',
    position_number,
    jsonb_build_object(
        'title',
        concept.title
    ),
    c.component_id
FROM virtual_dom_nodes section
JOIN components c
    ON c.component_name = 'ConceptCard'
CROSS JOIN (
    VALUES
        (0, 'Component Architecture'),
        (1, 'JSX'),
        (2, 'Virtual DOM'),
        (3, 'Rendering')
) AS concept(position_number, title)
WHERE section.element_tag = 'section';


-- =========================================================
-- 22. INITIAL RENDER
-- =========================================================

INSERT INTO render_operations (
    application_id,
    tree_id,
    render_status
)
SELECT
    application_id,
    tree_id,
    'PENDING'
FROM virtual_dom_trees
WHERE tree_version = 1;


-- =========================================================
-- 23. SAMPLE RENDER PATCHES
-- =========================================================

INSERT INTO dom_patches (
    render_id,
    patch_type,
    node_path,
    new_value
)
SELECT
    render_id,
    'INSERT',
    'root.0',
    '{"element": "header"}'::JSONB
FROM render_operations;

INSERT INTO dom_patches (
    render_id,
    patch_type,
    node_path,
    new_value
)
SELECT
    render_id,
    'INSERT',
    'root.1',
    '{"element": "section"}'::JSONB
FROM render_operations;


-- =========================================================
-- 24. COMPLETE INITIAL RENDER
-- =========================================================

CALL complete_render(
    (SELECT MIN(render_id) FROM render_operations),
    12.450
);


-- =========================================================
-- 25. STATE TRANSITION
-- =========================================================

DO $$
DECLARE
    v_component_id BIGINT;
    v_new_version BIGINT;
BEGIN
    SELECT component_id
    INTO v_component_id
    FROM components
    WHERE component_name = 'Counter';

    v_new_version := update_component_state(
        v_component_id,
        'count',
        '1'::JSONB,
        1
    );

    RAISE NOTICE
        'Counter state updated to version %',
        v_new_version;
END;
$$;


-- =========================================================
-- 26. RETRIEVAL QUERIES
-- =========================================================

-- Registered components

SELECT
    application_name,
    component_name,
    category,
    component_version,
    status
FROM component_catalog
ORDER BY application_name, component_name;

-- Application component hierarchy

WITH RECURSIVE component_tree AS (
    SELECT
        c.component_id,
        c.component_name,
        0 AS depth,
        ARRAY[c.component_id] AS visited
    FROM components c
    WHERE c.component_name = 'App'

    UNION ALL

    SELECT
        child.component_id,
        child.component_name,
        parent.depth + 1,
        parent.visited || child.component_id
    FROM component_tree parent
    JOIN component_dependencies d
        ON d.parent_component_id = parent.component_id
    JOIN components child
        ON child.component_id = d.child_component_id
    WHERE NOT child.component_id = ANY(parent.visited)
)
SELECT
    component_name,
    depth
FROM component_tree
ORDER BY depth, component_name;


-- =========================================================
-- 27. VIRTUAL DOM TREE RETRIEVAL
-- =========================================================

SELECT
    t.tree_version,
    n.node_id,
    n.parent_node_id,
    n.node_kind,
    n.element_tag,
    n.text_content,
    n.child_position,
    n.props
FROM virtual_dom_trees t
JOIN virtual_dom_nodes n
    ON n.tree_id = t.tree_id
ORDER BY
    t.tree_version,
    n.parent_node_id NULLS FIRST,
    n.child_position;


-- =========================================================
-- 28. COMPONENT PROP VALIDATION
-- =========================================================

SELECT
    c.component_name,
    p.prop_name,
    p.data_type,
    p.is_required,
    p.default_value
FROM component_props p
JOIN components c
    ON c.component_id = p.component_id
ORDER BY c.component_name, p.prop_name;


-- =========================================================
-- 29. RENDER AGGREGATION
-- =========================================================

SELECT *
FROM render_performance;


-- =========================================================
-- 30. RENDER FAILURE RETRIEVAL
-- =========================================================

SELECT
    render_id,
    application_id,
    render_status,
    error_message,
    started_at
FROM render_operations
WHERE render_status = 'FAILED'
ORDER BY started_at DESC;


-- =========================================================
-- 31. STATE RETRIEVAL
-- =========================================================

SELECT
    c.component_name,
    s.state_key,
    s.state_value,
    s.state_version,
    s.updated_at
FROM component_state s
JOIN components c
    ON c.component_id = s.component_id
ORDER BY c.component_name;


-- =========================================================
-- 32. RENDER ELIGIBILITY EVALUATION
-- =========================================================

SELECT
    c.component_name,
    c.status,
    CASE
        WHEN c.status = 'ACTIVE' THEN 'ELIGIBLE'
        WHEN c.status = 'DEPRECATED' THEN 'WARNING'
        ELSE 'NOT_ELIGIBLE'
    END AS render_eligibility
FROM components c
ORDER BY c.component_name;


-- =========================================================
-- 33. VALIDATION: DUPLICATE SIBLING POSITIONS
-- =========================================================

SELECT
    tree_id,
    parent_node_id,
    child_position,
    COUNT(*) AS duplicate_count
FROM virtual_dom_nodes
WHERE parent_node_id IS NOT NULL
GROUP BY
    tree_id,
    parent_node_id,
    child_position
HAVING COUNT(*) > 1;


-- =========================================================
-- 34. VALIDATION: COMPONENT DEPENDENCY CYCLES
-- =========================================================

WITH RECURSIVE dependency_walk AS (
    SELECT
        parent_component_id AS start_component,
        child_component_id AS current_component,
        ARRAY[
            parent_component_id,
            child_component_id
        ] AS path,
        parent_component_id = child_component_id AS cycle_found
    FROM component_dependencies

    UNION ALL

    SELECT
        walk.start_component,
        d.child_component_id,
        walk.path || d.child_component_id,
        d.child_component_id = ANY(walk.path)
    FROM dependency_walk walk
    JOIN component_dependencies d
        ON d.parent_component_id = walk.current_component
    WHERE NOT walk.cycle_found
      AND cardinality(walk.path) < 100
)
SELECT DISTINCT
    start_component,
    path
FROM dependency_walk
WHERE cycle_found;


-- =========================================================
-- 35. COMPONENT USAGE REPORT
-- =========================================================

SELECT
    c.component_name,
    c.category,
    COUNT(n.node_id) AS node_usage_count,
    COUNT(DISTINCT n.tree_id) AS tree_usage_count
FROM components c
LEFT JOIN virtual_dom_nodes n
    ON n.component_id = c.component_id
GROUP BY
    c.component_id,
    c.component_name,
    c.category
ORDER BY node_usage_count DESC;


-- =========================================================
-- 36. TRANSACTION FAILURE EXAMPLE
-- =========================================================

-- The exception is caught inside the PL/pgSQL block.
-- The invalid state change is rolled back to the savepoint
-- established by the exception block.

DO $$
BEGIN
    BEGIN
        UPDATE component_state
        SET
            state_value = '-1'::JSONB,
            state_version = state_version + 1
        WHERE state_key = 'count'
          AND component_id = (
              SELECT component_id
              FROM components
              WHERE component_name = 'Counter'
          );

        RAISE EXCEPTION
            'Simulated application validation failure.';

    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Rejected state transaction: %',
                SQLERRM;
    END;
END;
$$;


-- =========================================================
-- 37. DATABASE STATISTICS
-- =========================================================

SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'react_learning'
ORDER BY tablename, indexname;


COMMIT;

-- =========================================================
-- END OF REACT INTRODUCTION DATABASE
-- =========================================================
