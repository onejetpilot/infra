CREATE TABLE IF NOT EXISTS training.duplicate_lab (
    ingest_id bigint PRIMARY KEY,
    business_key text NOT NULL,
    value text,
    updated_at timestamp NOT NULL,
    is_deleted boolean NOT NULL DEFAULT false,
    source text NOT NULL
);

TRUNCATE training.duplicate_lab;

INSERT INTO training.duplicate_lab (
    ingest_id, business_key, value, updated_at, is_deleted, source
)
VALUES
    (1,  'A', 'alpha',   '2024-01-01 10:00', false, 'api'),
    (2,  'A', 'alpha',   '2024-01-01 10:00', false, 'api'),
    (3,  'A', 'alpha-2', '2024-02-01 10:00', false, 'api'),
    (4,  'B', NULL,      '2024-01-05 09:00', false, 'csv'),
    (5,  'B', 'bravo',   '2024-01-05 09:00', false, 'api'),
    (6,  'B', 'bravo',   '2024-03-01 09:00', false, 'api'),
    (7,  'C', 'charlie', '2024-01-10 12:00', false, 'csv'),
    (8,  'C', 'charlie', '2024-02-10 12:00', true,  'api'),
    (9,  'D', 'delta-1', '2024-04-01 08:00', false, 'csv'),
    (10, 'D', 'delta-2', '2024-04-01 08:00', false, 'api'),
    (11, 'E', 'echo',    '2024-05-01 08:00', false, 'api'),
    (12, 'F', NULL,      '2024-05-02 08:00', false, 'csv');

CREATE TABLE IF NOT EXISTS training.dedup_watermark (
    pipeline_name text PRIMARY KEY,
    last_updated_at timestamp NOT NULL,
    last_ingest_id bigint NOT NULL
);

INSERT INTO training.dedup_watermark (
    pipeline_name, last_updated_at, last_ingest_id
)
VALUES ('duplicate_lab', '2024-02-01 10:00', 3)
ON CONFLICT (pipeline_name) DO UPDATE
SET last_updated_at = EXCLUDED.last_updated_at,
    last_ingest_id = EXCLUDED.last_ingest_id;

CREATE OR REPLACE FUNCTION training.dedup_view_exists(p_task_no integer)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'training'
          AND c.relname = format('dq_%s', lpad(p_task_no::text, 2, '0'))
          AND c.relkind = 'v'
    );
$$;

DELETE FROM training.task_tests WHERE module_name = 'deduplication';

INSERT INTO training.task_tests (
    module_name, task_no, test_no, test_name, actual_sql, expected_sql
)
SELECT
    'deduplication',
    task_no,
    1,
    'Представление создано с точным именем',
    format(
        'SELECT to_jsonb(training.dedup_view_exists(%s))',
        task_no
    ),
    'SELECT ''true''::jsonb'
FROM generate_series(1, 30) AS tasks(task_no);

INSERT INTO training.task_tests (
    module_name, task_no, test_no, test_name, actual_sql, expected_sql
)
VALUES
( 'deduplication', 1, 2, 'Найдены все повторяющиеся покупатели',
  $q$SELECT to_jsonb(NOT EXISTS (
      (SELECT customer_unique_id, count(*) AS rows_count
       FROM staging.customers GROUP BY customer_unique_id HAVING count(*) > 1
       EXCEPT SELECT customer_unique_id, rows_count FROM training.dq_01)
      UNION ALL
      (SELECT customer_unique_id, rows_count FROM training.dq_01
       EXCEPT
       SELECT customer_unique_id, count(*) AS rows_count
       FROM staging.customers GROUP BY customer_unique_id HAVING count(*) > 1)
  ))$q$,
  $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 2, 2, 'Корректная диагностика order_id',
  $q$SELECT to_jsonb(NOT EXISTS (
      (SELECT order_id, count(*) AS rows_count
       FROM raw.orders GROUP BY order_id HAVING count(*) > 1
       EXCEPT SELECT order_id, rows_count FROM training.dq_02)
      UNION ALL
      (SELECT order_id, rows_count FROM training.dq_02
       EXCEPT
       SELECT order_id, count(*) AS rows_count
       FROM raw.orders GROUP BY order_id HAVING count(*) > 1)
  ))$q$,
  $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 3, 2, 'Уникальный список штатов',
  $q$SELECT to_jsonb(
      (SELECT count(*) = count(DISTINCT state) FROM training.dq_03)
      AND NOT EXISTS (
          (SELECT DISTINCT state FROM staging.customers
           EXCEPT SELECT state FROM training.dq_03)
          UNION ALL
          (SELECT state FROM training.dq_03
           EXCEPT SELECT DISTINCT state FROM staging.customers)
      )
  )$q$,
  $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 4, 2, 'Одна геолокация на составной ключ',
  $q$SELECT to_jsonb(
      (SELECT count(*) = count(DISTINCT (zip_code_prefix, city)) FROM training.dq_04)
      AND NOT EXISTS (
          SELECT DISTINCT zip_code_prefix, city FROM staging.geolocation
          EXCEPT SELECT zip_code_prefix, city FROM training.dq_04
      )
  )$q$,
  $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 5, 2, 'Минимальный customer_id выбран детерминированно',
  $q$SELECT to_jsonb(NOT EXISTS (
      SELECT 1
      FROM training.dq_05 d
      JOIN (
          SELECT customer_unique_id, min(customer_id) AS expected_id
          FROM staging.customers GROUP BY customer_unique_id
      ) e USING (customer_unique_id)
      WHERE d.customer_id IS DISTINCT FROM e.expected_id
  ) AND (SELECT count(*) = count(DISTINCT customer_unique_id) FROM training.dq_05))$q$,
  $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 6, 2, 'Нумерация не имеет разрывов',
  $q$SELECT to_jsonb(NOT EXISTS (
      SELECT 1 FROM (
          SELECT customer_unique_id, min(rn) min_rn, max(rn) max_rn, count(*) n
          FROM training.dq_06 GROUP BY customer_unique_id
      ) x WHERE min_rn <> 1 OR max_rn <> n
  ) AND (SELECT count(*) FROM training.dq_06) = (SELECT count(*) FROM staging.customers))$q$,
  $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 7, 2, 'Возвращены только лишние строки',
  $q$SELECT to_jsonb(
      (SELECT bool_and(rn > 1) FROM training.dq_07)
      AND (SELECT count(*) FROM training.dq_07)
          = (SELECT count(*) - count(DISTINCT customer_unique_id) FROM staging.customers)
  )$q$,
  $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 8, 2, 'Выбран максимальный платёж заказа',
  $q$SELECT to_jsonb(
      (SELECT count(*) = count(DISTINCT order_id) FROM training.dq_08)
      AND NOT EXISTS (
          SELECT 1 FROM training.dq_08 d
          JOIN (
              SELECT order_id, max(payment_value) expected_value
              FROM staging.order_payments GROUP BY order_id
          ) e USING (order_id)
          WHERE d.payment_value IS DISTINCT FROM e.expected_value
      )
  )$q$,
  $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 9, 2, 'Одна позиция на заказ и товар',
  $q$SELECT to_jsonb(
      (SELECT count(*) = count(DISTINCT (order_id, product_id)) FROM training.dq_09)
      AND NOT EXISTS (
          SELECT 1 FROM training.dq_09 d
          JOIN (
              SELECT order_id, product_id, min(order_item_id) expected_id
              FROM staging.order_items GROUP BY order_id, product_id
          ) e USING (order_id, product_id)
          WHERE d.order_item_id IS DISTINCT FROM e.expected_id
      )
  )$q$,
  $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 10, 2, 'Выбран последний отзыв',
  $q$SELECT to_jsonb(
      (SELECT count(*) = count(DISTINCT order_id) FROM training.dq_10)
      AND NOT EXISTS (
          SELECT 1 FROM training.dq_10 d
          JOIN (
              SELECT order_id, max(answered_at) expected_at
              FROM staging.order_reviews GROUP BY order_id
          ) e USING (order_id)
          WHERE d.answered_at IS DISTINCT FROM e.expected_at
      )
  )$q$,
  $q$SELECT 'true'::jsonb$q$ );

INSERT INTO training.task_tests (
    module_name, task_no, test_no, test_name, actual_sql, expected_sql
)
VALUES
( 'deduplication', 11, 2, 'Полные дубли найдены',
  $q$SELECT to_jsonb(NOT EXISTS (
      (SELECT business_key, value, updated_at, is_deleted, source, count(*) rows_count
       FROM training.duplicate_lab
       GROUP BY business_key, value, updated_at, is_deleted, source
       HAVING count(*) > 1
       EXCEPT SELECT business_key, value, updated_at, is_deleted, source, rows_count FROM training.dq_11)
      UNION ALL
      (SELECT business_key, value, updated_at, is_deleted, source, rows_count FROM training.dq_11
       EXCEPT
       SELECT business_key, value, updated_at, is_deleted, source, count(*) rows_count
       FROM training.duplicate_lab
       GROUP BY business_key, value, updated_at, is_deleted, source
       HAVING count(*) > 1)
  ))$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 12, 2, 'Полные повторы удалены логически',
  $q$SELECT to_jsonb(NOT EXISTS (
      (SELECT DISTINCT business_key, value, updated_at, is_deleted, source FROM training.duplicate_lab
       EXCEPT SELECT business_key, value, updated_at, is_deleted, source FROM training.dq_12)
      UNION ALL
      (SELECT business_key, value, updated_at, is_deleted, source FROM training.dq_12
       EXCEPT SELECT DISTINCT business_key, value, updated_at, is_deleted, source FROM training.duplicate_lab)
  ))$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 13, 2, 'Выбрана последняя версия',
  $q$SELECT to_jsonb(
      (SELECT array_agg(ingest_id ORDER BY business_key) FROM training.dq_13)
      = ARRAY[3,6,8,10,11,12]::bigint[]
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 14, 2, 'Выбрана первая версия',
  $q$SELECT to_jsonb(
      (SELECT array_agg(ingest_id ORDER BY business_key) FROM training.dq_14)
      = ARRAY[1,4,7,9,11,12]::bigint[]
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 15, 2, 'Применён приоритет заполненности',
  $q$SELECT to_jsonb(
      (SELECT array_agg(ingest_id ORDER BY business_key) FROM training.dq_15)
      = ARRAY[3,6,8,10,11,12]::bigint[]
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 16, 2, 'Конфликтующие значения посчитаны',
  $q$SELECT to_jsonb(
      (SELECT jsonb_object_agg(business_key, distinct_values_count) FROM training.dq_16)
      = '{"A":2,"D":2}'::jsonb
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 17, 2, 'Границы истории корректны',
  $q$SELECT to_jsonb(
      (SELECT sum(versions_count) FROM training.dq_17) = 12
      AND NOT EXISTS (
          SELECT 1 FROM training.dq_17 d
          JOIN (
              SELECT business_key, count(*) versions_count,
                     min(updated_at) first_updated_at, max(updated_at) last_updated_at
              FROM training.duplicate_lab GROUP BY business_key
          ) e USING (business_key)
          WHERE (d.versions_count, d.first_updated_at, d.last_updated_at)
             IS DISTINCT FROM
                (e.versions_count, e.first_updated_at, e.last_updated_at)
      )
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 18, 2, 'Сопоставлены raw и distinct',
  $q$SELECT to_jsonb(
      (SELECT total_rows = 12 AND distinct_rows = 11 FROM training.dq_18)
      AND (SELECT count(*) = 1 FROM training.dq_18)
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 19, 2, 'Рассчитан процент лишних ключевых версий',
  $q$SELECT to_jsonb(
      (SELECT duplicate_pct = round(100.0 * (12 - 6) / 12, 2) FROM training.dq_19)
      AND (SELECT count(*) = 1 FROM training.dq_19)
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 20, 2, 'Обнаружена ничья последних версий',
  $q$SELECT to_jsonb(
      (SELECT jsonb_object_agg(business_key, latest_rows_count) FROM training.dq_20)
      = '{"D":2}'::jsonb
  )$q$, $q$SELECT 'true'::jsonb$q$ );

INSERT INTO training.task_tests (
    module_name, task_no, test_no, test_name, actual_sql, expected_sql
)
VALUES
( 'deduplication', 21, 2, 'Клиенты уникальны и выбраны по качеству',
  $q$SELECT to_jsonb(
      (SELECT count(*) = count(DISTINCT customer_unique_id) FROM training.dq_21)
      AND (SELECT count(*) FROM training.dq_21)
          = (SELECT count(DISTINCT customer_unique_id) FROM staging.customers)
      AND NOT EXISTS (
          SELECT 1 FROM training.dq_21 d
          WHERE EXISTS (
              SELECT 1 FROM staging.customers s
              WHERE s.customer_unique_id = d.customer_unique_id
                AND ((s.city IS NOT NULL)::int + (s.state IS NOT NULL)::int)
                    > ((d.city IS NOT NULL)::int + (d.state IS NOT NULL)::int)
          )
      )
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 22, 2, 'По zip-коду выбраны модальные координаты',
  $q$SELECT to_jsonb(
      (SELECT count(*) = count(DISTINCT zip_code_prefix) FROM training.dq_22)
      AND NOT EXISTS (
          SELECT 1
          FROM training.dq_22 d
          JOIN (
              SELECT zip_code_prefix, max(freq) max_freq
              FROM (
                  SELECT zip_code_prefix, latitude, longitude, count(*) freq
                  FROM staging.geolocation
                  GROUP BY zip_code_prefix, latitude, longitude
              ) f GROUP BY zip_code_prefix
          ) m USING (zip_code_prefix)
          JOIN (
              SELECT zip_code_prefix, latitude, longitude, count(*) freq
              FROM staging.geolocation
              GROUP BY zip_code_prefix, latitude, longitude
          ) chosen
            ON chosen.zip_code_prefix = d.zip_code_prefix
           AND chosen.latitude = d.latitude
           AND chosen.longitude = d.longitude
          WHERE chosen.freq <> m.max_freq
      )
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 23, 2, 'Товары имеют уникальный product_id',
  $q$SELECT to_jsonb(
      (SELECT count(*) = count(DISTINCT product_id) FROM training.dq_23)
      AND (SELECT count(*) FROM training.dq_23)
          = (SELECT count(DISTINCT product_id) FROM staging.products)
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 24, 2, 'Канонический платёж и итог согласованы',
  $q$SELECT to_jsonb(
      (SELECT count(*) = count(DISTINCT order_id) FROM training.dq_24)
      AND NOT EXISTS (
          SELECT 1 FROM training.dq_24 d
          JOIN (
              SELECT order_id, max(payment_value) max_payment,
                     sum(payment_value) total_payment
              FROM staging.order_payments GROUP BY order_id
          ) e USING (order_id)
          WHERE d.payment_value IS DISTINCT FROM e.max_payment
             OR d.total_payment_value IS DISTINCT FROM e.total_payment
      )
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 25, 2, 'Потенциальные повторы отзывов имеют rows_count',
  $q$SELECT to_jsonb(
      (SELECT bool_and(rows_count > 1) FROM training.dq_25)
      AND NOT EXISTS (
          SELECT order_id, review_score,
                 lower(trim(coalesce(review_message,''))) normalized_message,
                 count(*) rows_count
          FROM staging.order_reviews
          GROUP BY order_id, review_score,
                   lower(trim(coalesce(review_message,'')))
          HAVING count(*) > 1
          EXCEPT
          SELECT order_id, review_score, normalized_message, rows_count
          FROM training.dq_25
      )
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 26, 2, 'Каждая версия сопоставлена последней',
  $q$SELECT to_jsonb(
      (SELECT count(*) = 12 FROM training.dq_26)
      AND NOT EXISTS (
          SELECT 1 FROM training.dq_26 d
          JOIN training.duplicate_lab src USING (ingest_id)
          JOIN (
              SELECT DISTINCT ON (business_key) business_key, ingest_id canonical_ingest_id
              FROM training.duplicate_lab
              ORDER BY business_key, updated_at DESC, ingest_id DESC
          ) c USING (business_key)
          WHERE d.canonical_ingest_id <> c.canonical_ingest_id
      )
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 27, 2, 'Сохранено происхождение версий',
  $q$SELECT to_jsonb(NOT EXISTS (
      SELECT 1 FROM training.dq_27 d
      JOIN (
          SELECT business_key, array_agg(ingest_id ORDER BY ingest_id) ingest_ids
          FROM training.duplicate_lab GROUP BY business_key
      ) e USING (business_key)
      WHERE d.ingest_ids IS DISTINCT FROM e.ingest_ids
  ) AND (SELECT count(*) = 6 FROM training.dq_27))$q$,
  $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 28, 2, 'Tombstone применён после выбора версии',
  $q$SELECT to_jsonb(
      (SELECT array_agg(ingest_id ORDER BY business_key) FROM training.dq_28)
      = ARRAY[3,6,10,11,12]::bigint[]
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 29, 2, 'Watermark учитывает timestamp и ingest_id',
  $q$SELECT to_jsonb(
      (SELECT array_agg(ingest_id ORDER BY ingest_id) FROM training.dq_29)
      = ARRAY[4,5,6,7,8,9,10,11,12]::bigint[]
  )$q$, $q$SELECT 'true'::jsonb$q$ ),
( 'deduplication', 30, 2, 'Итоговые показатели качества согласованы',
  $q$SELECT to_jsonb(
      (SELECT total_rows = 12
          AND unique_keys = 6
          AND duplicate_rows = 6
          AND conflict_keys = 2
          AND duplicate_pct = 50.00
       FROM training.dq_30)
      AND (SELECT count(*) = 1 FROM training.dq_30)
  )$q$, $q$SELECT 'true'::jsonb$q$ );
