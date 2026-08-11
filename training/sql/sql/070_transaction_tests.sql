CREATE TABLE IF NOT EXISTS training.tx_accounts (
    account_id integer PRIMARY KEY,
    owner_name text NOT NULL,
    balance numeric(14,2) NOT NULL CHECK (balance >= 0)
);

CREATE TABLE IF NOT EXISTS training.tx_operations (
    operation_id text PRIMARY KEY,
    from_account integer REFERENCES training.tx_accounts(account_id),
    to_account integer REFERENCES training.tx_accounts(account_id),
    amount numeric(14,2) NOT NULL CHECK (amount > 0),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS training.tx_events (
    event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_name text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS training.tx_jobs (
    job_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payload jsonb NOT NULL,
    status text NOT NULL DEFAULT 'new',
    worker_name text,
    processed_at timestamptz
);

CREATE TABLE IF NOT EXISTS training.tx_doctors (
    doctor_id integer PRIMARY KEY,
    doctor_name text NOT NULL,
    on_call boolean NOT NULL
);

CREATE TABLE IF NOT EXISTS training.tx_observations (
    task_no integer PRIMARY KEY CHECK (task_no BETWEEN 1 AND 30),
    observation jsonb NOT NULL,
    saved_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE OR REPLACE PROCEDURE training.reset_tx_lab()
LANGUAGE plpgsql
AS $$
BEGIN
    TRUNCATE training.tx_operations, training.tx_accounts;
    TRUNCATE training.tx_events RESTART IDENTITY;
    TRUNCATE training.tx_jobs RESTART IDENTITY;
    TRUNCATE training.tx_doctors;

    INSERT INTO training.tx_accounts(account_id, owner_name, balance)
    VALUES
        (1, 'Alice', 1000.00),
        (2, 'Bob',   1000.00),
        (3, 'Carol',  500.00);

    INSERT INTO training.tx_jobs(payload)
    VALUES
        ('{"job":"one"}'),
        ('{"job":"two"}'),
        ('{"job":"three"}'),
        ('{"job":"four"}');

    INSERT INTO training.tx_doctors(doctor_id, doctor_name, on_call)
    VALUES
        (1, 'Doctor A', true),
        (2, 'Doctor B', true);
END;
$$;

CREATE OR REPLACE FUNCTION training.save_tx_observation(
    p_task_no integer,
    p_observation jsonb
)
RETURNS void
LANGUAGE plpgsql
VOLATILE
AS $$
BEGIN
    IF p_task_no NOT BETWEEN 1 AND 30 THEN
        RAISE EXCEPTION 'Task number must be between 1 and 30';
    END IF;

    IF p_observation IS NULL
       OR jsonb_typeof(p_observation) <> 'object' THEN
        RAISE EXCEPTION 'Observation must be a JSON object';
    END IF;

    INSERT INTO training.tx_observations(task_no, observation, saved_at)
    VALUES (p_task_no, p_observation, clock_timestamp())
    ON CONFLICT (task_no) DO UPDATE
    SET observation = EXCLUDED.observation,
        saved_at = EXCLUDED.saved_at;
END;
$$;

CREATE OR REPLACE FUNCTION training.tx_observation_has_contract(p_task_no integer)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(
        (
            SELECT observation ?& ARRAY[
                       'session_a',
                       'session_b',
                       'result',
                       'explanation',
                       'steps'
                   ]
               AND length(trim(observation ->> 'explanation')) >= 20
               AND jsonb_typeof(observation -> 'steps') = 'array'
               AND jsonb_array_length(observation -> 'steps') > 0
            FROM training.tx_observations
            WHERE task_no = p_task_no
        ),
        false
    );
$$;

CREATE OR REPLACE FUNCTION training.tx_observation_has_expected_result(p_task_no integer)
RETURNS boolean
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    result jsonb;
    steps jsonb;
BEGIN
    SELECT observation -> 'result', observation -> 'steps'
      INTO result, steps
      FROM training.tx_observations
     WHERE task_no = p_task_no;

    IF result IS NULL OR jsonb_typeof(result) <> 'object'
       OR steps IS NULL OR jsonb_typeof(steps) <> 'array'
       OR jsonb_array_length(steps) < (CASE WHEN p_task_no >= 11 THEN 4 ELSE 2 END) THEN
        RETURN false;
    END IF;

    RETURN CASE p_task_no
        WHEN 1  THEN result @> '{"total_preserved":true,"committed":true}'
        WHEN 2  THEN result @> '{"balances_restored":true,"rolled_back":true}'
        WHEN 3  THEN result @> '{"savepoint_used":true,"outer_committed":true}'
        WHEN 4  THEN result @> '{"commit_visible":true,"rollback_invisible":true}'
        WHEN 5  THEN result @> '{"negative_balance_rejected":true}'
        WHEN 6  THEN result @> '{"duplicate_prevented":true,"charged_once":true}'
        WHEN 7  THEN result @> '{"balance_and_audit_atomic":true}'
        WHEN 8  THEN result @> '{"constraint_deferred":true,"commit_valid":true}'
        WHEN 9  THEN result @> '{"unique_conflict_recovered":true,"outer_committed":true}'
        WHEN 10 THEN result @> '{"own_uncommitted_visible":true,"other_session_visible":false}'
        WHEN 11 THEN result @> '{"dirty_read":false,"effective_level":"read committed"}'
        WHEN 12 THEN result @> '{"non_repeatable_read":true}'
        WHEN 13 THEN result @> '{"non_repeatable_read":false}'
        WHEN 14 THEN result @> '{"phantom_read":true}'
        WHEN 15 THEN result @> '{"phantom_read":false}'
        WHEN 16 THEN result @> '{"lost_update_reproduced":true}'
        WHEN 17 THEN result @> '{"lost_update_prevented":true,"method":"atomic update"}'
        WHEN 18 THEN result @> '{"lost_update_prevented":true,"method":"for update"}'
        WHEN 19 THEN result @> '{"second_update_waited":true}'
        WHEN 20 THEN result @> '{"sqlstate":"55P03"}'
        WHEN 21 THEN result @> '{"workers_selected_different_jobs":true}'
        WHEN 22 THEN result @> '{"sqlstate":"40P01"}'
        WHEN 23 THEN result @> '{"deadlock":false,"ordered_locking":true}'
        WHEN 24 THEN result @> '{"sqlstate":"55P03","local_timeout_used":true}'
        WHEN 25 THEN result @> '{"first_lock":true,"second_lock":false}'
        WHEN 26 THEN result @> '{"write_skew_reproduced":true,"invariant_broken":true}'
        WHEN 27 THEN result @> '{"sqlstate":"40001","invariant_preserved":true}'
        WHEN 28 THEN result @> '{"retry_on_40001":true,"eventually_succeeded":true}'
        WHEN 29 THEN result @> '{"blocker_found":true,"blocked_pid_found":true}'
        WHEN 30 THEN result @> '{"total_preserved":true,"negative_balances":false}'
        ELSE false
    END;
END;
$$;

CALL training.reset_tx_lab();

DELETE FROM training.task_tests WHERE module_name = 'transactions';

INSERT INTO training.task_tests (
    module_name, task_no, test_no, test_name, actual_sql, expected_sql
)
SELECT
    'transactions',
    task_no,
    1,
    'Наблюдение эксперимента сохранено',
    format(
        'SELECT to_jsonb(training.tx_observation_has_contract(%s))',
        task_no
    ),
    'SELECT ''true''::jsonb'
FROM generate_series(1, 30) AS tasks(task_no);

INSERT INTO training.task_tests (
    module_name, task_no, test_no, test_name, actual_sql, expected_sql
)
SELECT
    'transactions',
    task_no,
    2,
    'Вывод эксперимента соответствует контракту задания',
    format(
        'SELECT to_jsonb(training.tx_observation_has_expected_result(%s))',
        task_no
    ),
    'SELECT ''true''::jsonb'
FROM generate_series(1, 30) AS tasks(task_no);
