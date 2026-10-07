DROP SCHEMA IF EXISTS function_learning CASCADE;
CREATE SCHEMA function_learning;

SET search_path TO function_learning;

-- PostgreSQL functions demonstrate reusable behavior with typed parameters
-- and explicit return types.

CREATE OR REPLACE FUNCTION calculate_total(
    p_price NUMERIC,
    p_quantity INTEGER DEFAULT 1
)
RETURNS NUMERIC
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_price < 0 THEN
        RAISE EXCEPTION 'price cannot be negative';
    END IF;

    IF p_quantity < 0 THEN
        RAISE EXCEPTION 'quantity cannot be negative';
    END IF;

    RETURN p_price * p_quantity;
END;
$$;

CREATE OR REPLACE FUNCTION calculate_discount(
    p_amount NUMERIC,
    p_rate NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_amount < 0 THEN
        RAISE EXCEPTION 'amount cannot be negative';
    END IF;

    IF p_rate < 0 OR p_rate > 1 THEN
        RAISE EXCEPTION 'rate must be between 0 and 1';
    END IF;

    RETURN p_amount * (1 - p_rate);
END;
$$;

CREATE TABLE employees (
    employee_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_name TEXT NOT NULL,
    salary NUMERIC(12, 2) NOT NULL CHECK (salary >= 0)
);

INSERT INTO employees (employee_name, salary)
VALUES
    ('Ravi', 60000.00),
    ('Meera', 75000.00),
    ('Arun', 50000.00);

-- A SQL function can encapsulate a business calculation while accepting
-- values from relational data.
CREATE OR REPLACE FUNCTION net_salary(
    p_salary NUMERIC,
    p_bonus NUMERIC DEFAULT 0,
    p_tax_rate NUMERIC DEFAULT 0.20
)
RETURNS NUMERIC
LANGUAGE plpgsql
AS $$
DECLARE
    gross_salary NUMERIC;
BEGIN
    IF p_salary < 0 OR p_bonus < 0 THEN
        RAISE EXCEPTION 'salary and bonus cannot be negative';
    END IF;

    IF p_tax_rate < 0 OR p_tax_rate > 1 THEN
        RAISE EXCEPTION 'tax rate must be between 0 and 1';
    END IF;

    gross_salary := p_salary + p_bonus;

    RETURN gross_salary * (1 - p_tax_rate);
END;
$$;

-- A set-returning function demonstrates a function whose result behaves
-- like a relational table.
CREATE OR REPLACE FUNCTION employees_above_salary(
    p_minimum_salary NUMERIC
)
RETURNS TABLE (
    employee_id BIGINT,
    employee_name TEXT,
    salary NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        e.employee_id,
        e.employee_name,
        e.salary
    FROM employees AS e
    WHERE e.salary >= p_minimum_salary
    ORDER BY e.salary DESC;
$$;

-- A function can return a boolean decision rather than transformed data.
CREATE OR REPLACE FUNCTION valid_salary(
    p_salary NUMERIC
)
RETURNS BOOLEAN
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT p_salary IS NOT NULL
       AND p_salary >= 0;
$$;

-- Function-based queries.
SELECT calculate_total(250.00, 3) AS total;

SELECT calculate_total(100.00) AS total_using_default_quantity;

SELECT calculate_discount(1000.00, 0.15) AS discounted_amount;

SELECT
    employee_name,
    salary,
    net_salary(salary, 5000.00, 0.20) AS estimated_net_salary
FROM employees
ORDER BY employee_id;

SELECT *
FROM employees_above_salary(60000.00);

SELECT
    employee_name,
    valid_salary(salary) AS salary_is_valid
FROM employees;

-- Common table expressions can prepare relational data that is then
-- consumed by a function.
WITH payroll AS (
    SELECT
        employee_id,
        employee_name,
        salary,
        salary + 5000.00 AS gross_salary
    FROM employees
)
SELECT
    employee_name,
    gross_salary,
    calculate_discount(gross_salary, 0.20) AS after_tax_estimate
FROM payroll
ORDER BY employee_id;

-- PostgreSQL function volatility describes how the database may reason
-- about a function. valid_salary is IMMUTABLE because its result depends
-- only on its argument. employees_above_salary is STABLE because it reads
-- database state but does not modify it.

-- Demonstrate transactional use of a function-backed calculation.
BEGIN;

INSERT INTO employees (employee_name, salary)
VALUES ('Temporary Employee', 55000.00);

SELECT
    employee_name,
    net_salary(salary, 2500.00, 0.20) AS calculated_net_salary
FROM employees
WHERE employee_name = 'Temporary Employee';

ROLLBACK;

-- The rollback means Temporary Employee is not persisted.
SELECT *
FROM employees
WHERE employee_name = 'Temporary Employee';

-- The following examples intentionally raise errors when executed
-- individually. They demonstrate database-level validation rather than
-- silently producing invalid business results.
--
-- SELECT calculate_total(-10.00, 2);
-- SELECT calculate_discount(1000.00, 1.50);
-- SELECT net_salary(-500.00, 0, 0.20);

-- Function parameters are part of the function contract. PostgreSQL
-- resolves calls using their names, types, defaults, and return behavior.
SELECT calculate_total(p_price => 125.00, p_quantity => 4);

-- Aggregation can combine function results with relational operations.
SELECT
    COUNT(*) AS employee_count,
    SUM(salary) AS total_salary,
    AVG(net_salary(salary, 0, 0.20)) AS average_estimated_net_salary
FROM employees;

-- A function may also be used in a WHERE predicate when the function
-- expresses a domain-specific validation rule.
SELECT employee_id, employee_name, salary
FROM employees
WHERE valid_salary(salary)
ORDER BY salary DESC;
