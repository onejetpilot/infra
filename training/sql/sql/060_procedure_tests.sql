CREATE TABLE IF NOT EXISTS training.procedure_log (
    log_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_name text,
    message text,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    amount numeric,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS training.customer_work (
    customer_unique_id text PRIMARY KEY,
    city text,
    state text,
    loaded_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS training.order_work (
    order_id text PRIMARY KEY,
    customer_id text,
    order_status text,
    purchased_at timestamp,
    order_total numeric,
    processed_at timestamptz
);

CREATE TABLE IF NOT EXISTS training.order_archive (
    LIKE training.order_work INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS training.order_totals (
    order_id text PRIMARY KEY,
    order_total numeric NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS training.state_summary (
    state text PRIMARY KEY,
    orders_count bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS training.monthly_work (
    month_start date PRIMARY KEY,
    orders_count bigint NOT NULL,
    revenue numeric
);

CREATE TABLE IF NOT EXISTS training.customer_snapshot (
    as_of_date date NOT NULL,
    customer_unique_id text NOT NULL,
    orders_count bigint NOT NULL,
    PRIMARY KEY (as_of_date, customer_unique_id)
);

CREATE OR REPLACE FUNCTION training.procedure_is_valid(p_signature text)
RETURNS boolean
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_oid oid;
BEGIN
    v_oid := to_regprocedure(p_signature);
    RETURN v_oid IS NOT NULL
       AND EXISTS (
            SELECT 1
            FROM pg_proc
            WHERE oid = v_oid
              AND prokind = 'p'
       );
END;
$$;

DELETE FROM training.task_tests WHERE module_name = 'procedures';

INSERT INTO training.task_tests
    (module_name, task_no, test_no, test_name, actual_sql, expected_sql)
SELECT
    'procedures',
    task_no,
    1,
    'Процедура создана с точной сигнатурой',
    format(
        'SELECT to_jsonb(training.procedure_is_valid(%L))',
        signature
    ),
    'SELECT ''true''::jsonb'
FROM (
    VALUES
        (1,  'training.pr_01_log_message(text)'),
        (2,  'training.pr_02_log_event(text,jsonb)'),
        (3,  'training.pr_03_clear_log()'),
        (4,  'training.pr_04_add_customer(text,text,text)'),
        (5,  'training.pr_05_change_customer_city(text,text)'),
        (6,  'training.pr_06_delete_customer(text)'),
        (7,  'training.pr_07_upsert_customer(text,text,text)'),
        (8,  'training.pr_08_copy_customer(text)'),
        (9,  'training.pr_09_copy_state_customers(text)'),
        (10, 'training.pr_10_count_state_customers(text)'),
        (11, 'training.pr_11_refresh_order_sample(integer)'),
        (12, 'training.pr_12_load_orders_between(date,date)'),
        (13, 'training.pr_13_update_order_status(text,text)'),
        (14, 'training.pr_14_delete_cancelled_orders()'),
        (15, 'training.pr_15_mark_processed(text)'),
        (16, 'training.pr_16_reset_processing()'),
        (17, 'training.pr_17_load_order_total(text)'),
        (18, 'training.pr_18_load_customer_orders(text)'),
        (19, 'training.pr_19_rebuild_state_summary()'),
        (20, 'training.pr_20_refresh_month(date)'),
        (21, 'training.pr_21_validate_positive_amount(numeric)'),
        (22, 'training.pr_22_require_customer(text)'),
        (23, 'training.pr_23_move_customer(text,text)'),
        (24, 'training.pr_24_archive_old_orders(date)'),
        (25, 'training.pr_25_apply_discount(text,numeric)'),
        (26, 'training.pr_26_batch_log(text,integer)'),
        (27, 'training.pr_27_process_unhandled(integer)'),
        (28, 'training.pr_28_dynamic_clear(text)'),
        (29, 'training.pr_29_refresh_all()'),
        (30, 'training.pr_30_build_customer_snapshot(date)')
) AS signatures(task_no, signature);

CREATE OR REPLACE FUNCTION training.check_procedure_level1(p_task_no integer)
RETURNS boolean
LANGUAGE plpgsql
VOLATILE
AS $$
DECLARE
    v_customer record;
    v_expected bigint;
    v_before bigint;
BEGIN
    -- Каждая проверка начинает с чистой изменяемой песочницы.
    TRUNCATE training.procedure_log RESTART IDENTITY;
    TRUNCATE training.customer_work;

    CASE p_task_no
        WHEN 1 THEN
            CALL training.pr_01_log_message('automatic check');
            RETURN EXISTS (
                SELECT 1
                FROM training.procedure_log
                WHERE message = 'automatic check'
            );

        WHEN 2 THEN
            CALL training.pr_02_log_event('order_loaded', '{"order_id":"test-1"}'::jsonb);
            RETURN EXISTS (
                SELECT 1
                FROM training.procedure_log
                WHERE event_name = 'order_loaded'
                  AND payload = '{"order_id":"test-1"}'::jsonb
            );

        WHEN 3 THEN
            INSERT INTO training.procedure_log(message)
            VALUES ('first'), ('second');

            CALL training.pr_03_clear_log();
            RETURN NOT EXISTS (SELECT 1 FROM training.procedure_log);

        WHEN 4 THEN
            CALL training.pr_04_add_customer('check-customer', 'Moscow', 'MS');
            RETURN EXISTS (
                SELECT 1
                FROM training.customer_work
                WHERE customer_unique_id = 'check-customer'
                  AND city = 'Moscow'
                  AND state = 'MS'
            );

        WHEN 5 THEN
            INSERT INTO training.customer_work(customer_unique_id, city, state)
            VALUES ('check-customer', 'Old city', 'SP');

            CALL training.pr_05_change_customer_city('check-customer', 'New city');
            RETURN (
                SELECT city = 'New city' AND state = 'SP'
                FROM training.customer_work
                WHERE customer_unique_id = 'check-customer'
            );

        WHEN 6 THEN
            INSERT INTO training.customer_work(customer_unique_id, city, state)
            VALUES
                ('remove-me', 'A', 'SP'),
                ('keep-me', 'B', 'RJ');

            CALL training.pr_06_delete_customer('remove-me');
            RETURN NOT EXISTS (
                       SELECT 1 FROM training.customer_work
                       WHERE customer_unique_id = 'remove-me'
                   )
               AND EXISTS (
                       SELECT 1 FROM training.customer_work
                       WHERE customer_unique_id = 'keep-me'
                   );

        WHEN 7 THEN
            CALL training.pr_07_upsert_customer('upsert-me', 'First', 'SP');
            CALL training.pr_07_upsert_customer('upsert-me', 'Second', 'RJ');
            RETURN (
                SELECT count(*) = 1
                   AND min(city) = 'Second'
                   AND min(state) = 'RJ'
                FROM training.customer_work
                WHERE customer_unique_id = 'upsert-me'
            );

        WHEN 8 THEN
            SELECT customer_unique_id, city, state
            INTO v_customer
            FROM staging.customers
            ORDER BY customer_unique_id
            LIMIT 1;

            CALL training.pr_08_copy_customer(v_customer.customer_unique_id);
            CALL training.pr_08_copy_customer(v_customer.customer_unique_id);

            RETURN (
                SELECT count(*) = 1
                   AND min(city) = v_customer.city
                   AND min(state) = v_customer.state
                FROM training.customer_work
                WHERE customer_unique_id = v_customer.customer_unique_id
            );

        WHEN 9 THEN
            SELECT count(DISTINCT customer_unique_id)
            INTO v_expected
            FROM staging.customers
            WHERE state = 'AC';

            CALL training.pr_09_copy_state_customers('AC');
            CALL training.pr_09_copy_state_customers('AC');

            RETURN (
                SELECT count(*) = v_expected
                FROM training.customer_work
                WHERE state = 'AC'
            );

        WHEN 10 THEN
            SELECT count(*)
            INTO v_expected
            FROM staging.customers
            WHERE state = 'AC';

            SELECT count(*) INTO v_before
            FROM training.procedure_log;

            CALL training.pr_10_count_state_customers('AC');

            RETURN (
                SELECT count(*) = v_before + 1
                   AND bool_or(amount = v_expected)
                FROM training.procedure_log
            );

        ELSE
            RAISE EXCEPTION 'Level 1 has no task %', p_task_no;
    END CASE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN false;
END;
$$;

INSERT INTO training.task_tests
    (module_name, task_no, test_no, test_name, actual_sql, expected_sql)
SELECT
    'procedures',
    task_no,
    2,
    'Результат CALL и изменения данных',
    format(
        'SELECT to_jsonb(training.check_procedure_level1(%s))',
        task_no
    ),
    'SELECT ''true''::jsonb'
FROM generate_series(1, 10) AS tasks(task_no);

CREATE OR REPLACE FUNCTION training.check_procedure_level2(p_task_no integer)
RETURNS boolean
LANGUAGE plpgsql
VOLATILE
AS $$
DECLARE
    v_order_id text;
    v_customer_unique_id text;
    v_expected bigint;
    v_expected_total numeric;
BEGIN
    TRUNCATE training.order_work;
    TRUNCATE training.order_archive;
    TRUNCATE training.order_totals;
    TRUNCATE training.state_summary;
    TRUNCATE training.monthly_work;

    CASE p_task_no
        WHEN 11 THEN
            CALL training.pr_11_refresh_order_sample(3);
            RETURN (SELECT count(*) = 3 FROM training.order_work)
               AND NOT EXISTS (
                    (SELECT order_id FROM training.order_work)
                    EXCEPT
                    (SELECT order_id FROM staging.orders ORDER BY order_id LIMIT 3)
               );

        WHEN 12 THEN
            SELECT count(*)
            INTO v_expected
            FROM staging.orders
            WHERE purchased_at >= DATE '2018-01-01'
              AND purchased_at < DATE '2018-01-03';

            CALL training.pr_12_load_orders_between(DATE '2018-01-01', DATE '2018-01-03');
            CALL training.pr_12_load_orders_between(DATE '2018-01-01', DATE '2018-01-03');
            RETURN (SELECT count(*) = v_expected FROM training.order_work);

        WHEN 13 THEN
            SELECT order_id INTO v_order_id
            FROM staging.orders ORDER BY order_id LIMIT 1;

            INSERT INTO training.order_work(order_id, order_status)
            VALUES (v_order_id, 'created');

            CALL training.pr_13_update_order_status(v_order_id, 'delivered');
            RETURN (
                SELECT order_status = 'delivered'
                FROM training.order_work
                WHERE order_id = v_order_id
            );

        WHEN 14 THEN
            INSERT INTO training.order_work(order_id, order_status)
            VALUES
                ('cancel-me', 'canceled'),
                ('unavailable-me', 'unavailable'),
                ('keep-me', 'delivered');

            CALL training.pr_14_delete_cancelled_orders();
            RETURN (SELECT count(*) = 1 FROM training.order_work)
               AND EXISTS (
                    SELECT 1 FROM training.order_work
                    WHERE order_id = 'keep-me'
               );

        WHEN 15 THEN
            INSERT INTO training.order_work(order_id, order_status)
            VALUES ('process-me', 'delivered');

            CALL training.pr_15_mark_processed('process-me');
            RETURN (
                SELECT processed_at IS NOT NULL
                FROM training.order_work
                WHERE order_id = 'process-me'
            );

        WHEN 16 THEN
            INSERT INTO training.order_work(order_id, order_status, processed_at)
            VALUES
                ('one', 'delivered', clock_timestamp()),
                ('two', 'shipped', clock_timestamp());

            CALL training.pr_16_reset_processing();
            RETURN NOT EXISTS (
                SELECT 1 FROM training.order_work
                WHERE processed_at IS NOT NULL
            );

        WHEN 17 THEN
            SELECT order_id INTO v_order_id
            FROM staging.order_items ORDER BY order_id LIMIT 1;

            SELECT round(sum(price + freight_value), 2)
            INTO v_expected_total
            FROM staging.order_items
            WHERE order_id = v_order_id;

            CALL training.pr_17_load_order_total(v_order_id);
            CALL training.pr_17_load_order_total(v_order_id);
            RETURN (
                SELECT count(*) = 1
                   AND min(order_total) = v_expected_total
                FROM training.order_totals
                WHERE order_id = v_order_id
            );

        WHEN 18 THEN
            SELECT c.customer_unique_id
            INTO v_customer_unique_id
            FROM staging.customers c
            JOIN staging.orders o USING (customer_id)
            GROUP BY c.customer_unique_id
            ORDER BY count(*) DESC, c.customer_unique_id
            LIMIT 1;

            SELECT count(*)
            INTO v_expected
            FROM staging.orders o
            JOIN staging.customers c USING (customer_id)
            WHERE c.customer_unique_id = v_customer_unique_id;

            CALL training.pr_18_load_customer_orders(v_customer_unique_id);
            RETURN (SELECT count(*) = v_expected FROM training.order_work);

        WHEN 19 THEN
            CALL training.pr_19_rebuild_state_summary();
            RETURN NOT EXISTS (
                (
                    SELECT state, orders_count
                    FROM training.state_summary
                    EXCEPT
                    SELECT c.state, count(*)
                    FROM staging.orders o
                    JOIN staging.customers c USING (customer_id)
                    GROUP BY c.state
                )
                UNION ALL
                (
                    SELECT c.state, count(*)
                    FROM staging.orders o
                    JOIN staging.customers c USING (customer_id)
                    GROUP BY c.state
                    EXCEPT
                    SELECT state, orders_count
                    FROM training.state_summary
                )
            );

        WHEN 20 THEN
            CALL training.pr_20_refresh_month(DATE '2018-01-01');
            CALL training.pr_20_refresh_month(DATE '2018-01-01');
            RETURN (
                SELECT count(*) = 1
                   AND min(orders_count) = (
                        SELECT orders_count
                        FROM mart.monthly_sales
                        WHERE month = DATE '2018-01-01'
                   )
                FROM training.monthly_work
                WHERE month_start = DATE '2018-01-01'
            );

        ELSE
            RAISE EXCEPTION 'Level 2 has no task %', p_task_no;
    END CASE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN false;
END;
$$;

INSERT INTO training.task_tests
    (module_name, task_no, test_no, test_name, actual_sql, expected_sql)
SELECT
    'procedures',
    task_no,
    2,
    'Результат пакетной операции',
    format(
        'SELECT to_jsonb(training.check_procedure_level2(%s))',
        task_no
    ),
    'SELECT ''true''::jsonb'
FROM generate_series(11, 20) AS tasks(task_no);

CREATE OR REPLACE FUNCTION training.check_procedure_level3(p_task_no integer)
RETURNS boolean
LANGUAGE plpgsql
VOLATILE
AS $$
DECLARE
    v_raised boolean := false;
    v_customer_unique_id text;
    v_before numeric;
    v_expected bigint;
BEGIN
    TRUNCATE training.procedure_log RESTART IDENTITY;
    TRUNCATE training.customer_work;
    TRUNCATE training.order_work;
    TRUNCATE training.order_archive;
    TRUNCATE training.state_summary;
    TRUNCATE training.customer_snapshot;

    CASE p_task_no
        WHEN 21 THEN
            BEGIN
                CALL training.pr_21_validate_positive_amount(-1);
            EXCEPTION
                WHEN OTHERS THEN v_raised := true;
            END;

            CALL training.pr_21_validate_positive_amount(125.50);
            RETURN v_raised
               AND EXISTS (
                    SELECT 1 FROM training.procedure_log
                    WHERE amount = 125.50
               );

        WHEN 22 THEN
            SELECT customer_unique_id INTO v_customer_unique_id
            FROM mart.customer_summary
            ORDER BY customer_unique_id
            LIMIT 1;

            CALL training.pr_22_require_customer(v_customer_unique_id);
            BEGIN
                CALL training.pr_22_require_customer('__missing_customer__');
            EXCEPTION
                WHEN OTHERS THEN v_raised := true;
            END;
            RETURN v_raised;

        WHEN 23 THEN
            INSERT INTO training.customer_work(customer_unique_id, city, state)
            VALUES
                ('old-key', 'A', 'SP'),
                ('occupied-key', 'B', 'RJ');

            CALL training.pr_23_move_customer('old-key', 'new-key');
            BEGIN
                CALL training.pr_23_move_customer('new-key', 'occupied-key');
            EXCEPTION
                WHEN unique_violation THEN v_raised := true;
                WHEN OTHERS THEN v_raised := true;
            END;

            RETURN v_raised
               AND EXISTS (
                    SELECT 1 FROM training.customer_work
                    WHERE customer_unique_id = 'new-key'
               )
               AND EXISTS (
                    SELECT 1 FROM training.customer_work
                    WHERE customer_unique_id = 'occupied-key'
               );

        WHEN 24 THEN
            INSERT INTO training.order_work(order_id, purchased_at)
            VALUES
                ('old-order', DATE '2017-01-01'),
                ('new-order', DATE '2018-01-01');

            CALL training.pr_24_archive_old_orders(DATE '2017-06-01');
            RETURN EXISTS (
                       SELECT 1 FROM training.order_archive
                       WHERE order_id = 'old-order'
                   )
               AND NOT EXISTS (
                       SELECT 1 FROM training.order_work
                       WHERE order_id = 'old-order'
                   )
               AND EXISTS (
                       SELECT 1 FROM training.order_work
                       WHERE order_id = 'new-order'
                   );

        WHEN 25 THEN
            INSERT INTO training.order_work(
                order_id, customer_id, order_total
            )
            SELECT o.order_id, o.customer_id, 100
            FROM staging.orders o
            JOIN staging.customers c USING (customer_id)
            WHERE c.state IN ('AC', 'SP')
            ORDER BY c.state, o.order_id
            LIMIT 20;

            SELECT sum(order_total) INTO v_before
            FROM training.order_work ow
            JOIN staging.customers c USING (customer_id)
            WHERE c.state = 'AC';

            CALL training.pr_25_apply_discount('AC', 10);
            RETURN (
                SELECT sum(order_total) = round(v_before * 0.9, 2)
                FROM training.order_work ow
                JOIN staging.customers c USING (customer_id)
                WHERE c.state = 'AC'
            );

        WHEN 26 THEN
            CALL training.pr_26_batch_log('batch', 3);
            RETURN (
                SELECT count(*) = 3
                   AND bool_and(message IN ('batch_1', 'batch_2', 'batch_3'))
                FROM training.procedure_log
            );

        WHEN 27 THEN
            INSERT INTO training.order_work(order_id, purchased_at)
            VALUES
                ('order-3', DATE '2018-01-03'),
                ('order-1', DATE '2018-01-01'),
                ('order-2', DATE '2018-01-02');

            CALL training.pr_27_process_unhandled(2);
            RETURN (SELECT count(*) = 2 FROM training.order_work WHERE processed_at IS NOT NULL)
               AND EXISTS (
                    SELECT 1 FROM training.order_work
                    WHERE order_id = 'order-3' AND processed_at IS NULL
               );

        WHEN 28 THEN
            INSERT INTO training.procedure_log(message) VALUES ('delete me');
            INSERT INTO training.customer_work(customer_unique_id) VALUES ('keep me');

            CALL training.pr_28_dynamic_clear('procedure_log');
            RETURN NOT EXISTS (SELECT 1 FROM training.procedure_log)
               AND EXISTS (SELECT 1 FROM training.customer_work);

        WHEN 29 THEN
            CALL training.pr_29_refresh_all();
            RETURN EXISTS (SELECT 1 FROM training.order_work)
               AND (
                    SELECT count(*) = (
                        SELECT count(DISTINCT state)
                        FROM staging.customers
                    )
                    FROM training.state_summary
               );

        WHEN 30 THEN
            SELECT count(*)
            INTO v_expected
            FROM (
                SELECT c.customer_unique_id
                FROM staging.customers c
                JOIN staging.orders o USING (customer_id)
                WHERE o.purchased_at < DATE '2018-01-02'
                GROUP BY c.customer_unique_id
            ) AS customers;

            CALL training.pr_30_build_customer_snapshot(DATE '2018-01-01');
            CALL training.pr_30_build_customer_snapshot(DATE '2018-01-01');
            RETURN (
                SELECT count(*) = v_expected
                   AND bool_and(orders_count > 0)
                FROM training.customer_snapshot
                WHERE as_of_date = DATE '2018-01-01'
            );

        ELSE
            RAISE EXCEPTION 'Level 3 has no task %', p_task_no;
    END CASE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN false;
END;
$$;

INSERT INTO training.task_tests
    (module_name, task_no, test_no, test_name, actual_sql, expected_sql)
SELECT
    'procedures',
    task_no,
    2,
    'Побочные эффекты и граничные случаи',
    format(
        'SELECT to_jsonb(training.check_procedure_level3(%s))',
        task_no
    ),
    'SELECT ''true''::jsonb'
FROM generate_series(21, 30) AS tasks(task_no);
