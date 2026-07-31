CREATE SCHEMA IF NOT EXISTS training;

CREATE TABLE IF NOT EXISTS training.task_tests (
    module_name text NOT NULL,
    task_no integer NOT NULL,
    test_no integer NOT NULL,
    test_name text NOT NULL,
    actual_sql text NOT NULL,
    expected_sql text NOT NULL,
    PRIMARY KEY (module_name, task_no, test_no)
);

CREATE TABLE IF NOT EXISTS training.check_history (
    check_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    checked_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    module_name text NOT NULL,
    task_no integer NOT NULL,
    tests_passed integer NOT NULL,
    tests_total integer NOT NULL
);

CREATE OR REPLACE FUNCTION training.run_checks(
    p_module_name text,
    p_task_no integer
)
RETURNS TABLE (
    test_no integer,
    test_name text,
    status text,
    expected jsonb,
    actual jsonb,
    error_message text
)
LANGUAGE plpgsql
AS $$
DECLARE
    test_case record;
    actual_value jsonb;
    expected_value jsonb;
    passed integer := 0;
    total integer := 0;
BEGIN
    FOR test_case IN
        SELECT *
        FROM training.task_tests
        WHERE module_name = p_module_name
          AND task_no = p_task_no
        ORDER BY test_no
    LOOP
        total := total + 1;
        actual_value := NULL;
        expected_value := NULL;

        BEGIN
            EXECUTE test_case.expected_sql INTO expected_value;
            EXECUTE test_case.actual_sql INTO actual_value;

            IF actual_value IS NOT DISTINCT FROM expected_value THEN
                passed := passed + 1;
                RETURN QUERY
                SELECT
                    test_case.test_no,
                    test_case.test_name,
                    'PASS'::text,
                    expected_value,
                    actual_value,
                    NULL::text;
            ELSE
                RETURN QUERY
                SELECT
                    test_case.test_no,
                    test_case.test_name,
                    'FAIL'::text,
                    expected_value,
                    actual_value,
                    NULL::text;
            END IF;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN QUERY
                SELECT
                    test_case.test_no,
                    test_case.test_name,
                    'ERROR'::text,
                    expected_value,
                    actual_value,
                    SQLERRM::text;
        END;
    END LOOP;

    IF total = 0 THEN
        RAISE EXCEPTION
            'No tests registered for module %, task %',
            p_module_name,
            p_task_no;
    END IF;

    INSERT INTO training.check_history (
        module_name,
        task_no,
        tests_passed,
        tests_total
    )
    VALUES (
        p_module_name,
        p_task_no,
        passed,
        total
    );
END;
$$;

CREATE OR REPLACE VIEW training.progress AS
WITH latest_check AS (
    SELECT DISTINCT ON (module_name, task_no)
        module_name,
        task_no,
        checked_at,
        tests_passed,
        tests_total
    FROM training.check_history
    ORDER BY module_name, task_no, checked_at DESC
)
SELECT
    module_name,
    task_no,
    checked_at,
    tests_passed,
    tests_total,
    tests_passed = tests_total AS completed
FROM latest_check;

CREATE TABLE IF NOT EXISTS training.function_audit (
    audit_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_name text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

TRUNCATE training.task_tests;
TRUNCATE training.check_history RESTART IDENTITY;
TRUNCATE training.function_audit RESTART IDENTITY;
