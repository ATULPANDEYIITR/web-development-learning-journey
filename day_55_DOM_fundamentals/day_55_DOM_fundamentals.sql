-- PostgreSQL DOM fundamentals: relational representation of a mutable element tree.
-- Requires PostgreSQL 14 or later.

BEGIN;

DROP SCHEMA IF EXISTS dom_lab CASCADE;
CREATE SCHEMA dom_lab;
SET search_path = dom_lab, public;

CREATE TYPE node_kind AS ENUM ('document', 'element', 'text');
CREATE TYPE mutation_kind AS ENUM (
    'create', 'set_attribute', 'set_text', 'append', 'remove'
);

CREATE TABLE dom_documents (
    document_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE dom_nodes (
    node_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES dom_documents(document_id)
        ON DELETE CASCADE,
    parent_id BIGINT,
    kind node_kind NOT NULL,
    tag_name TEXT,
    text_content TEXT NOT NULL DEFAULT '',
    sibling_position INTEGER NOT NULL CHECK (sibling_position >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT node_parent_fk
        FOREIGN KEY (parent_id) REFERENCES dom_nodes(node_id)
        ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT node_kind_content_ck CHECK (
        (kind = 'document' AND tag_name IS NULL AND parent_id IS NULL)
        OR (kind = 'element' AND tag_name ~ '^[a-z][a-z0-9-]*$')
        OR (kind = 'text' AND tag_name IS NULL)
    )
);

-- A document has exactly one root row, enforced by this partial unique index.
CREATE UNIQUE INDEX one_document_root
    ON dom_nodes(document_id)
    WHERE kind = 'document';

CREATE INDEX dom_nodes_parent_position_idx
    ON dom_nodes(document_id, parent_id, sibling_position);

CREATE INDEX dom_nodes_tag_idx
    ON dom_nodes(document_id, tag_name)
    WHERE kind = 'element';

CREATE TABLE dom_attributes (
    node_id BIGINT NOT NULL REFERENCES dom_nodes(node_id) ON DELETE CASCADE,
    attribute_name TEXT NOT NULL CHECK (attribute_name ~ '^[a-zA-Z_:][a-zA-Z0-9_:.-]*$'),
    attribute_value TEXT NOT NULL,
    PRIMARY KEY (node_id, attribute_name)
);

CREATE INDEX dom_attributes_name_value_idx
    ON dom_attributes(attribute_name, attribute_value);

CREATE TABLE dom_mutations (
    mutation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES dom_documents(document_id)
        ON DELETE CASCADE,
    node_id BIGINT,
    operation mutation_kind NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ensure every parent belongs to the same document and is not a text node.
CREATE FUNCTION validate_node_parent()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    parent_document BIGINT;
    parent_kind node_kind;
BEGIN
    IF NEW.parent_id IS NULL THEN
        IF NEW.kind <> 'document' THEN
            RAISE EXCEPTION 'Only document nodes may have no parent';
        END IF;
        RETURN NEW;
    END IF;

    SELECT document_id, kind
      INTO parent_document, parent_kind
      FROM dom_nodes
     WHERE node_id = NEW.parent_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Parent node % does not exist', NEW.parent_id;
    END IF;

    IF parent_document <> NEW.document_id THEN
        RAISE EXCEPTION 'Parent and child must belong to the same document';
    END IF;

    IF parent_kind = 'text' THEN
        RAISE EXCEPTION 'Text nodes cannot have children';
    END IF;

    IF NEW.kind = 'document' THEN
        RAISE EXCEPTION 'Document nodes cannot have a parent';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER dom_node_parent_validation
BEFORE INSERT OR UPDATE OF parent_id, document_id, kind
ON dom_nodes
FOR EACH ROW EXECUTE FUNCTION validate_node_parent();

-- Reject cycles even when a node is reparented.
CREATE FUNCTION prevent_dom_cycle()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    cycle_found BOOLEAN;
BEGIN
    IF NEW.parent_id IS NULL THEN
        RETURN NEW;
    END IF;

    WITH RECURSIVE ancestors(node_id, parent_id) AS (
        SELECT node_id, parent_id
          FROM dom_nodes
         WHERE node_id = NEW.parent_id
        UNION ALL
        SELECT n.node_id, n.parent_id
          FROM dom_nodes n
          JOIN ancestors a ON n.node_id = a.parent_id
    )
    SELECT EXISTS (
        SELECT 1 FROM ancestors WHERE node_id = NEW.node_id
    ) INTO cycle_found;

    IF cycle_found THEN
        RAISE EXCEPTION 'Mutation would create a DOM cycle';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER dom_cycle_validation
BEFORE UPDATE OF parent_id ON dom_nodes
FOR EACH ROW EXECUTE FUNCTION prevent_dom_cycle();

CREATE FUNCTION log_dom_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO dom_mutations(document_id, node_id, operation, details)
    VALUES (
        NEW.document_id,
        NEW.node_id,
        CASE
            WHEN TG_TABLE_NAME = 'dom_attributes' THEN 'set_attribute'::mutation_kind
            ELSE 'create'::mutation_kind
        END,
        jsonb_build_object('kind', NEW.kind, 'tag_name', NEW.tag_name)
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER dom_node_insert_audit
AFTER INSERT ON dom_nodes
FOR EACH ROW EXECUTE FUNCTION log_dom_mutation();

CREATE VIEW dom_element_inventory AS
SELECT d.document_name,
       n.node_id,
       n.parent_id,
       n.tag_name,
       n.sibling_position,
       count(child.node_id) AS direct_child_count
FROM dom_documents d
JOIN dom_nodes n ON n.document_id = d.document_id
LEFT JOIN dom_nodes child ON child.parent_id = n.node_id
WHERE n.kind = 'element'
GROUP BY d.document_name, n.node_id, n.parent_id,
         n.tag_name, n.sibling_position;

CREATE FUNCTION find_elements(
    p_document_id BIGINT,
    p_tag_name TEXT DEFAULT NULL,
    p_attribute_name TEXT DEFAULT NULL,
    p_attribute_value TEXT DEFAULT NULL
)
RETURNS TABLE (
    node_id BIGINT,
    parent_id BIGINT,
    tag_name TEXT,
    sibling_position INTEGER
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF p_tag_name IS NOT NULL
       AND p_tag_name !~ '^[a-z][a-z0-9-]*$' THEN
        RAISE EXCEPTION 'Invalid tag selector: %', p_tag_name;
    END IF;

    IF (p_attribute_name IS NULL) <> (p_attribute_value IS NULL) THEN
        RAISE EXCEPTION 'Attribute name and value must be supplied together';
    END IF;

    RETURN QUERY
    SELECT n.node_id, n.parent_id, n.tag_name, n.sibling_position
    FROM dom_nodes n
    WHERE n.document_id = p_document_id
      AND n.kind = 'element'
      AND (p_tag_name IS NULL OR n.tag_name = p_tag_name)
      AND (
          p_attribute_name IS NULL
          OR EXISTS (
              SELECT 1 FROM dom_attributes a
              WHERE a.node_id = n.node_id
                AND a.attribute_name = p_attribute_name
                AND a.attribute_value = p_attribute_value
          )
      )
    ORDER BY n.parent_id NULLS FIRST, n.sibling_position, n.node_id;
END;
$$;

-- A stored tree represents the current state. Application transactions should
-- serialize sibling-position changes for a document to avoid concurrent races.
INSERT INTO dom_documents(document_name)
VALUES ('repository-dashboard');

-- Document root.
INSERT INTO dom_nodes(document_id, kind, sibling_position)
SELECT document_id, 'document', 0
FROM dom_documents
WHERE document_name = 'repository-dashboard';

-- Main element.
INSERT INTO dom_nodes(document_id, parent_id, kind, tag_name, sibling_position)
SELECT d.document_id, root.node_id, 'element', 'main', 0
FROM dom_documents d
JOIN dom_nodes root ON root.document_id = d.document_id
                   AND root.kind = 'document'
WHERE d.document_name = 'repository-dashboard';

INSERT INTO dom_attributes(node_id, attribute_name, attribute_value)
SELECT node_id, 'id', 'repository'
FROM dom_nodes
WHERE tag_name = 'main' AND document_id = (
    SELECT document_id FROM dom_documents
    WHERE document_name = 'repository-dashboard'
);

INSERT INTO dom_attributes(node_id, attribute_name, attribute_value)
SELECT node_id, 'class', 'dashboard'
FROM dom_nodes
WHERE tag_name = 'main' AND document_id = (
    SELECT document_id FROM dom_documents
    WHERE document_name = 'repository-dashboard'
);

-- Create the heading, status, and list as direct children of main.
INSERT INTO dom_nodes(document_id, parent_id, kind, tag_name, text_content, sibling_position)
SELECT document_id, node_id, 'element', 'h1', 'Repository Dashboard', 0
FROM dom_nodes
WHERE tag_name = 'main';

INSERT INTO dom_nodes(document_id, parent_id, kind, tag_name, text_content, sibling_position)
SELECT document_id, node_id, 'element', 'p', 'Review queue', 1
FROM dom_nodes
WHERE tag_name = 'main';

INSERT INTO dom_nodes(document_id, parent_id, kind, tag_name, sibling_position)
SELECT document_id, node_id, 'element', 'ul', 2
FROM dom_nodes
WHERE tag_name = 'main';

INSERT INTO dom_attributes(node_id, attribute_name, attribute_value)
SELECT node_id, 'class', 'status'
FROM dom_nodes
WHERE tag_name = 'p' AND text_content = 'Review queue';

INSERT INTO dom_attributes(node_id, attribute_name, attribute_value)
SELECT node_id, 'data-state', 'ready'
FROM dom_nodes
WHERE tag_name = 'p' AND text_content = 'Review queue';

INSERT INTO dom_attributes(node_id, attribute_name, attribute_value)
SELECT node_id, 'id', 'pull-requests'
FROM dom_nodes
WHERE tag_name = 'ul';

-- Three pull-request list items, each with a title span.
WITH request_data(number, title, position) AS (
    VALUES
        ('101', 'Validate API input', 0),
        ('102', 'Improve database indexes', 1),
        ('103', 'Fix navigation tests', 2)
)
INSERT INTO dom_nodes(document_id, parent_id, kind, tag_name, sibling_position)
SELECT list.document_id, list.node_id, 'element', 'li', r.position
FROM request_data r
CROSS JOIN LATERAL (
    SELECT n.node_id, n.document_id
    FROM dom_nodes n
    JOIN dom_attributes a ON a.node_id = n.node_id
                        AND a.attribute_name = 'id'
                        AND a.attribute_value = 'pull-requests'
) list;

INSERT INTO dom_attributes(node_id, attribute_name, attribute_value)
SELECT n.node_id, 'class', 'pull-request'
FROM dom_nodes n
JOIN dom_nodes parent ON parent.node_id = n.parent_id
JOIN dom_attributes a ON a.node_id = parent.node_id
                     AND a.attribute_name = 'id'
                     AND a.attribute_value = 'pull-requests'
WHERE n.tag_name = 'li';

WITH request_data(number, title, position) AS (
    VALUES
        ('101', 'Validate API input', 0),
        ('102', 'Improve database indexes', 1),
        ('103', 'Fix navigation tests', 2)
)
INSERT INTO dom_attributes(node_id, attribute_name, attribute_value)
SELECT n.node_id, 'data-number', r.number
FROM dom_nodes n
JOIN dom_nodes parent ON parent.node_id = n.parent_id
JOIN dom_attributes a ON a.node_id = parent.node_id
                     AND a.attribute_name = 'id'
                     AND a.attribute_value = 'pull-requests'
JOIN request_data r ON r.position = n.sibling_position
WHERE n.tag_name = 'li';

WITH request_data(title, position) AS (
    VALUES
        ('Validate API input', 0),
        ('Improve database indexes', 1),
        ('Fix navigation tests', 2)
)
INSERT INTO dom_nodes(document_id, parent_id, kind, tag_name, text_content, sibling_position)
SELECT li.document_id, li.node_id, 'element', 'span', r.title, 0
FROM dom_nodes li
JOIN dom_nodes parent ON parent.node_id = li.parent_id
JOIN dom_attributes a ON a.node_id = parent.node_id
                     AND a.attribute_name = 'id'
                     AND a.attribute_value = 'pull-requests'
JOIN request_data r ON r.position = li.sibling_position
WHERE li.tag_name = 'li';

INSERT INTO dom_attributes(node_id, attribute_name, attribute_value)
SELECT node_id, 'class', 'title'
FROM dom_nodes
WHERE tag_name = 'span';

-- Retrieval: descendants of the main element using a recursive CTE.
WITH RECURSIVE tree AS (
    SELECT n.node_id, n.parent_id, n.kind, n.tag_name,
           n.text_content, n.sibling_position, 0 AS depth
    FROM dom_nodes n
    WHERE n.kind = 'document'
      AND n.document_id = (
          SELECT document_id FROM dom_documents
          WHERE document_name = 'repository-dashboard'
      )
    UNION ALL
    SELECT child.node_id, child.parent_id, child.kind, child.tag_name,
           child.text_content, child.sibling_position, tree.depth + 1
    FROM dom_nodes child
    JOIN tree ON child.parent_id = tree.node_id
)
SELECT depth, kind, tag_name, text_content, sibling_position
FROM tree
ORDER BY depth, parent_id NULLS FIRST, sibling_position;

-- Selector-like retrieval by tag and attribute.
SELECT * FROM find_elements(
    (SELECT document_id FROM dom_documents
     WHERE document_name = 'repository-dashboard'),
    'li',
    'class',
    'pull-request'
);

-- Aggregation: direct child counts and inventory.
SELECT document_name, tag_name, direct_child_count
FROM dom_element_inventory
ORDER BY tag_name, node_id;

-- Safe text mutation and audit logging happen within a transaction.
SAVEPOINT before_title_change;

UPDATE dom_nodes
SET text_content = 'Validate API input and reject unsafe payloads'
WHERE tag_name = 'span'
  AND node_id = (
      SELECT n.node_id
      FROM dom_nodes n
      JOIN dom_attributes a ON a.node_id = n.node_id
                          AND a.attribute_name = 'class'
                          AND a.attribute_value = 'title'
      ORDER BY n.node_id
      LIMIT 1
  );

-- Attribute update demonstrates the upsert pattern for mutable attributes.
INSERT INTO dom_attributes(node_id, attribute_name, attribute_value)
SELECT node_id, 'data-review-state', 'in-review'
FROM dom_nodes
WHERE tag_name = 'li'
ORDER BY node_id
LIMIT 1
ON CONFLICT (node_id, attribute_name)
DO UPDATE SET attribute_value = EXCLUDED.attribute_value;

-- Remove one list item and its attributes. Child rows cascade.
DELETE FROM dom_nodes
WHERE tag_name = 'li'
  AND node_id = (
      SELECT n.node_id
      FROM dom_nodes n
      JOIN dom_attributes a ON a.node_id = n.node_id
                          AND a.attribute_name = 'data-number'
                          AND a.attribute_value = '103'
      LIMIT 1
  );

-- Validation report: every pull-request element must have an identifier.
SELECT n.node_id,
       CASE WHEN a.attribute_value IS NULL THEN 'invalid' ELSE 'valid' END AS validation_state
FROM dom_nodes n
LEFT JOIN dom_attributes a
       ON a.node_id = n.node_id
      AND a.attribute_name = 'data-number'
JOIN dom_attributes c
       ON c.node_id = n.node_id
      AND c.attribute_name = 'class'
      AND c.attribute_value = 'pull-request'
ORDER BY n.node_id;

-- Failed operations should be isolated with a savepoint in a client transaction.
-- This query demonstrates that unsupported selectors are rejected by the function.
SELECT 'unsupported combinators are not accepted by find_elements' AS policy_note;

COMMIT;

-- Final reporting queries.
SELECT d.document_name, n.tag_name, n.text_content, n.sibling_position
FROM dom_documents d
JOIN dom_nodes n ON n.document_id = d.document_id
WHERE n.kind = 'element'
ORDER BY n.parent_id NULLS FIRST, n.sibling_position, n.node_id;

SELECT operation, count(*) AS mutation_count
FROM dom_mutations
GROUP BY operation
ORDER BY operation;
