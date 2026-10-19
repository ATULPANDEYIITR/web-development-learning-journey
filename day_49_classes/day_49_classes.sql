-- PostgreSQL-compatible relational model for a class catalog.
-- The database represents classes as persisted domain definitions and
-- instances as objects created from those definitions.
-- Class-level attributes model static members; object-level attributes model
-- instance state. Foreign keys and CHECK constraints enforce class invariants.

DROP SCHEMA IF EXISTS class_management CASCADE;
CREATE SCHEMA class_management;
SET search_path TO class_management;

CREATE TYPE member_kind AS ENUM (
    'INSTANCE_FIELD',
    'STATIC_FIELD',
    'INSTANCE_METHOD',
    'STATIC_METHOD'
);

CREATE TYPE visibility_level AS ENUM (
    'PUBLIC',
    'PROTECTED',
    'PRIVATE'
);

CREATE TYPE object_status AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'ARCHIVED'
);

CREATE TABLE class_definition (
    class_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    class_name varchar(100) NOT NULL UNIQUE,
    parent_class_id bigint REFERENCES class_definition(class_id)
        ON DELETE RESTRICT,
    is_abstract boolean NOT NULL DEFAULT false,
    description text NOT NULL,
    CONSTRAINT class_name_format
        CHECK (class_name ~ '^[A-Za-z][A-Za-z0-9_]*$')
);

CREATE TABLE class_member (
    member_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    class_id bigint NOT NULL
        REFERENCES class_definition(class_id)
        ON DELETE CASCADE,
    member_name varchar(100) NOT NULL,
    member_kind member_kind NOT NULL,
    visibility visibility_level NOT NULL,
    data_type varchar(100),
    default_value text,
    CONSTRAINT unique_class_member
        UNIQUE (class_id, member_name),
    CONSTRAINT field_type_required
        CHECK (
            member_kind NOT IN ('INSTANCE_FIELD', 'STATIC_FIELD')
            OR data_type IS NOT NULL
        )
);

CREATE TABLE class_method (
    method_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    class_id bigint NOT NULL
        REFERENCES class_definition(class_id)
        ON DELETE CASCADE,
    method_name varchar(100) NOT NULL,
    return_type varchar(100) NOT NULL,
    is_static boolean NOT NULL DEFAULT false,
    is_abstract boolean NOT NULL DEFAULT false,
    CONSTRAINT unique_class_method
        UNIQUE (class_id, method_name)
);

CREATE TABLE object_instance (
    object_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    class_id bigint NOT NULL
        REFERENCES class_definition(class_id)
        ON DELETE RESTRICT,
    object_name varchar(150) NOT NULL,
    status object_status NOT NULL DEFAULT 'ACTIVE',
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT unique_object_name
        UNIQUE (class_id, object_name)
);

CREATE TABLE instance_field_value (
    object_id bigint NOT NULL
        REFERENCES object_instance(object_id)
        ON DELETE CASCADE,
    member_id bigint NOT NULL
        REFERENCES class_member(member_id)
        ON DELETE CASCADE,
    value_text text,
    PRIMARY KEY (object_id, member_id)
);

CREATE TABLE static_field_value (
    class_id bigint NOT NULL
        REFERENCES class_definition(class_id)
        ON DELETE CASCADE,
    member_id bigint NOT NULL
        REFERENCES class_member(member_id)
        ON DELETE CASCADE,
    value_text text,
    PRIMARY KEY (class_id, member_id)
);

CREATE INDEX idx_class_parent
    ON class_definition(parent_class_id);

CREATE INDEX idx_class_member_kind
    ON class_member(class_id, member_kind);

CREATE INDEX idx_object_class_status
    ON object_instance(class_id, status);

CREATE INDEX idx_instance_field_member
    ON instance_field_value(member_id);

-- The class hierarchy demonstrates inheritance:
-- Account is the parent, SavingsAccount and BusinessAccount are children.
INSERT INTO class_definition
    (class_name, parent_class_id, is_abstract, description)
VALUES
    (
        'Account',
        NULL,
        true,
        'Abstract base class for accounts with protected lifecycle rules.'
    );

INSERT INTO class_definition
    (class_name, parent_class_id, is_abstract, description)
SELECT
    'SavingsAccount',
    class_id,
    false,
    'Account with a minimum balance and interest behavior.'
FROM class_definition
WHERE class_name = 'Account';

INSERT INTO class_definition
    (class_name, parent_class_id, is_abstract, description)
SELECT
    'BusinessAccount',
    class_id,
    false,
    'Account supporting transfers and business transaction charges.'
FROM class_definition
WHERE class_name = 'Account';

INSERT INTO class_member
    (class_id, member_name, member_kind, visibility, data_type)
SELECT
    class_id,
    '__account_id',
    'INSTANCE_FIELD',
    'PRIVATE',
    'bigint'
FROM class_definition
WHERE class_name = 'Account';

INSERT INTO class_member
    (class_id, member_name, member_kind, visibility, data_type)
SELECT
    class_id,
    '__owner',
    'INSTANCE_FIELD',
    'PRIVATE',
    'varchar(150)'
FROM class_definition
WHERE class_name = 'Account';

INSERT INTO class_member
    (class_id, member_name, member_kind, visibility, data_type)
SELECT
    class_id,
    '__balance',
    'INSTANCE_FIELD',
    'PRIVATE',
    'numeric(14,2)'
FROM class_definition
WHERE class_name = 'Account';

INSERT INTO class_member
    (class_id, member_name, member_kind, visibility, data_type)
SELECT
    class_id,
    'active_accounts',
    'STATIC_FIELD',
    'PRIVATE',
    'integer'
FROM class_definition
WHERE class_name = 'Account';

INSERT INTO class_member
    (class_id, member_name, member_kind, visibility, data_type, default_value)
SELECT
    class_id,
    'INTEREST_RATE',
    'STATIC_FIELD',
    'PUBLIC',
    'numeric(6,4)',
    '0.0400'
FROM class_definition
WHERE class_name = 'SavingsAccount';

INSERT INTO class_member
    (class_id, member_name, member_kind, visibility, data_type, default_value)
SELECT
    class_id,
    'TRANSACTION_FEE',
    'STATIC_FIELD',
    'PUBLIC',
    'numeric(10,2)',
    '2.50'
FROM class_definition
WHERE class_name = 'BusinessAccount';

INSERT INTO class_method
    (class_id, method_name, return_type, is_static, is_abstract)
SELECT
    class_id,
    'monthly_charge',
    'numeric(10,2)',
    false,
    true
FROM class_definition
WHERE class_name = 'Account';

INSERT INTO class_method
    (class_id, method_name, return_type, is_static)
SELECT
    class_id,
    'active_accounts',
    'integer',
    true
FROM class_definition
WHERE class_name = 'Account';

INSERT INTO class_method
    (class_id, method_name, return_type, is_static)
SELECT
    class_id,
    'apply_interest',
    'void',
    false
FROM class_definition
WHERE class_name = 'SavingsAccount';

INSERT INTO class_method
    (class_id, method_name, return_type, is_static)
SELECT
    class_id,
    'transfer_to',
    'void',
    false
FROM class_definition
WHERE class_name = 'BusinessAccount';

-- Concrete instances represent objects created from classes.
INSERT INTO object_instance
    (class_id, object_name)
SELECT class_id, 'Asha Savings'
FROM class_definition
WHERE class_name = 'SavingsAccount';

INSERT INTO object_instance
    (class_id, object_name)
SELECT class_id, 'Northwind Business'
FROM class_definition
WHERE class_name = 'BusinessAccount';

INSERT INTO instance_field_value
    (object_id, member_id, value_text)
SELECT
    o.object_id,
    m.member_id,
    'Asha Sharma'
FROM object_instance o
JOIN class_definition c
    ON c.class_id = o.class_id
JOIN class_member m
    ON m.class_id = c.class_id
WHERE o.object_name = 'Asha Savings'
  AND m.member_name = '__owner';

INSERT INTO instance_field_value
    (object_id, member_id, value_text)
SELECT
    o.object_id,
    m.member_id,
    '5000.00'
FROM object_instance o
JOIN class_definition c
    ON c.class_id = o.class_id
JOIN class_member m
    ON m.class_id = c.class_id
WHERE o.object_name = 'Asha Savings'
  AND m.member_name = '__balance';

INSERT INTO instance_field_value
    (object_id, member_id, value_text)
SELECT
    o.object_id,
    m.member_id,
    'Northwind Traders'
FROM object_instance o
JOIN class_definition c
    ON c.class_id = o.class_id
JOIN class_member m
    ON m.class_id = c.class_id
WHERE o.object_name = 'Northwind Business'
  AND m.member_name = '__owner';

INSERT INTO instance_field_value
    (object_id, member_id, value_text)
SELECT
    o.object_id,
    m.member_id,
    '15000.00'
FROM object_instance o
JOIN class_definition c
    ON c.class_id = o.class_id
JOIN class_member m
    ON m.class_id = c.class_id
WHERE o.object_name = 'Northwind Business'
  AND m.member_name = '__balance';

-- Static fields belong to a class, not to an individual object.
INSERT INTO static_field_value
    (class_id, member_id, value_text)
SELECT
    c.class_id,
    m.member_id,
    '0'
FROM class_definition c
JOIN class_member m
    ON m.class_id = c.class_id
WHERE c.class_name = 'Account'
  AND m.member_name = 'active_accounts';

INSERT INTO static_field_value
    (class_id, member_id, value_text)
SELECT
    c.class_id,
    m.member_id,
    '0.0400'
FROM class_definition c
JOIN class_member m
    ON m.class_id = c.class_id
WHERE c.class_name = 'SavingsAccount'
  AND m.member_name = 'INTEREST_RATE';

INSERT INTO static_field_value
    (class_id, member_id, value_text)
SELECT
    c.class_id,
    m.member_id,
    '2.50'
FROM class_definition c
JOIN class_member m
    ON m.class_id = c.class_id
WHERE c.class_name = 'BusinessAccount'
  AND m.member_name = 'TRANSACTION_FEE';

-- This view exposes inherited class relationships without copying members
-- from Account into every subclass.
CREATE OR REPLACE VIEW effective_class_members AS
WITH RECURSIVE hierarchy AS (
    SELECT
        class_id,
        class_id AS effective_class_id,
        class_name,
        parent_class_id
    FROM class_definition

    UNION ALL

    SELECT
        parent.class_id,
        hierarchy.effective_class_id,
        parent.class_name,
        parent.parent_class_id
    FROM class_definition parent
    JOIN hierarchy
        ON hierarchy.parent_class_id = parent.class_id
)
SELECT
    h.effective_class_id AS class_id,
    target.class_name AS concrete_class,
    h.class_id AS declared_class_id,
    h.class_name AS declared_class,
    m.member_name,
    m.member_kind,
    m.visibility,
    m.data_type
FROM hierarchy h
JOIN class_definition target
    ON target.class_id = h.effective_class_id
JOIN class_member m
    ON m.class_id = h.class_id;

-- Show each concrete class with inherited and locally declared members.
SELECT
    concrete_class,
    declared_class,
    member_name,
    member_kind,
    visibility,
    data_type
FROM effective_class_members
WHERE concrete_class IN ('SavingsAccount', 'BusinessAccount')
ORDER BY concrete_class, declared_class, member_name;

-- Show objects together with their private instance state.
SELECT
    o.object_name,
    c.class_name,
    o.status,
    MAX(
        CASE
            WHEN m.member_name = '__owner'
            THEN v.value_text
        END
    ) AS owner,
    MAX(
        CASE
            WHEN m.member_name = '__balance'
            THEN v.value_text
        END
    )::numeric AS balance
FROM object_instance o
JOIN class_definition c
    ON c.class_id = o.class_id
LEFT JOIN instance_field_value v
    ON v.object_id = o.object_id
LEFT JOIN class_member m
    ON m.member_id = v.member_id
GROUP BY o.object_id, o.object_name, c.class_name, o.status
ORDER BY o.object_id;

-- Static state is queried independently because it belongs to the class.
SELECT
    c.class_name,
    m.member_name,
    m.member_kind,
    m.visibility,
    s.value_text
FROM static_field_value s
JOIN class_definition c
    ON c.class_id = s.class_id
JOIN class_member m
    ON m.member_id = s.member_id
ORDER BY c.class_name, m.member_name;

-- A transaction demonstrates controlled lifecycle changes to an object.
BEGIN;

UPDATE object_instance
SET status = 'INACTIVE'
WHERE object_name = 'Northwind Business'
  AND status = 'ACTIVE';

UPDATE instance_field_value v
SET value_text = '0.00'
FROM object_instance o
JOIN class_definition c
    ON c.class_id = o.class_id
JOIN class_member m
    ON m.class_id = c.class_id
WHERE v.object_id = o.object_id
  AND v.member_id = m.member_id
  AND o.object_name = 'Northwind Business'
  AND m.member_name = '__balance';

COMMIT;

-- The database can expose potentially invalid class metadata.
-- This query finds private fields whose declared data type is missing.
SELECT
    c.class_name,
    m.member_name
FROM class_member m
JOIN class_definition c
    ON c.class_id = m.class_id
WHERE m.visibility = 'PRIVATE'
  AND m.data_type IS NULL;

-- Demonstrate the inheritance tree.
WITH RECURSIVE class_tree AS (
    SELECT
        class_id,
        class_name,
        parent_class_id,
        0 AS depth
    FROM class_definition
    WHERE parent_class_id IS NULL

    UNION ALL

    SELECT
        child.class_id,
        child.class_name,
        child.parent_class_id,
        parent.depth + 1
    FROM class_definition child
    JOIN class_tree parent
        ON child.parent_class_id = parent.class_id
)
SELECT
    repeat('  ', depth) || class_name AS hierarchy,
    depth,
    class_id
FROM class_tree
ORDER BY depth, class_id;
