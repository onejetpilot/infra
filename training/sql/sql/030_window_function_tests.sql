CREATE OR REPLACE FUNCTION training.window_view_exists(p_task_no integer)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'training'
          AND c.relname = format('wf_%s', lpad(p_task_no::text, 2, '0'))
          AND c.relkind = 'v'
    );
$$;

DELETE FROM training.task_tests WHERE module_name = 'window_functions';

INSERT INTO training.task_tests (
    module_name, task_no, test_no, test_name, actual_sql, expected_sql
)
SELECT
    'window_functions',
    task_no,
    1,
    'Представление создано с точным именем',
    format(
        'SELECT to_jsonb(training.window_view_exists(%s))',
        task_no
    ),
    'SELECT ''true''::jsonb'
FROM generate_series(1, 30) AS tasks(task_no);

INSERT INTO training.task_tests
    (module_name, task_no, test_no, test_name, actual_sql, expected_sql)
VALUES
('window_functions', 1, 2, 'Глобальная нумерация непрерывна',
 $q$SELECT to_jsonb(
   (SELECT count(*) = count(DISTINCT row_num) FROM training.wf_01)
   AND (SELECT min(row_num)=1 AND max(row_num)=count(*) FROM training.wf_01)
   AND (SELECT count(*) FROM training.wf_01)=(SELECT count(*) FROM staging.orders)
 )$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 2, 2, 'Нумерация начинается заново для статуса',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM (
     SELECT order_status, min(row_num) lo, max(row_num) hi, count(*) n
     FROM training.wf_02 GROUP BY order_status
   ) x WHERE lo<>1 OR hi<>n
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 5, 2, 'Не более трёх заказов каждого штата',
 $q$SELECT to_jsonb(
   NOT EXISTS (SELECT state FROM training.wf_05 GROUP BY state HAVING count(*)>3)
   AND (SELECT bool_and(row_num BETWEEN 1 AND 3) FROM training.wf_05)
 )$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 6, 2, 'Один первый заказ покупателя',
 $q$SELECT to_jsonb(
   (SELECT count(*)=count(DISTINCT customer_unique_id) FROM training.wf_06)
   AND (SELECT count(*) FROM training.wf_06)
       =(SELECT count(DISTINCT customer_unique_id) FROM staging.customers)
 )$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 8, 2, 'Предыдущая покупка не позже текущей',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM training.wf_08 WHERE previous_purchased_at > purchased_at
 ))$q$, $q$SELECT 'true'::jsonb$q$);

INSERT INTO training.task_tests
    (module_name, task_no, test_no, test_name, actual_sql, expected_sql)
VALUES
('window_functions', 3, 2, 'Dense rank начинается с единицы без разрывов',
 $q$SELECT to_jsonb(
   (SELECT min(payment_rank)=1 FROM training.wf_03)
   AND NOT EXISTS (
     SELECT 1 FROM generate_series(
       1,(SELECT max(payment_rank) FROM training.wf_03)
     ) n WHERE NOT EXISTS (
       SELECT 1 FROM training.wf_03 WHERE payment_rank=n
     )
   )
 )$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 4, 2, 'Три вида ранга согласованы',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM training.wf_04
   WHERE row_num < payment_rank OR payment_rank < dense_payment_rank
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 7, 2, 'Последняя покупка выбрана правильно',
 $q$SELECT to_jsonb(NOT EXISTS (
   (SELECT customer_unique_id, purchased_at FROM training.wf_07
    EXCEPT
    SELECT customer_unique_id, last_order_at FROM mart.customer_summary)
   UNION ALL
   (SELECT customer_unique_id, last_order_at FROM mart.customer_summary
    EXCEPT
    SELECT customer_unique_id, purchased_at FROM training.wf_07)
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 9, 2, 'Интервал соседних покупок неотрицательный',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM training.wf_09 WHERE days_since_previous < 0
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 10, 2, 'Следующая покупка не раньше текущей',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM training.wf_10 WHERE next_purchased_at < purchased_at
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 11, 2, 'Накопительная выручка монотонна',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM (
     SELECT revenue_running,
            lag(revenue_running) OVER(ORDER BY sale_date) prev
     FROM training.wf_11
   ) x WHERE revenue_running < prev
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 15, 2, 'Итог категории одинаков для её строк',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT category_name_english
   FROM training.wf_15
   GROUP BY category_name_english
   HAVING min(category_revenue) IS DISTINCT FROM max(category_revenue)
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 16, 2, 'Доли категории дают сто процентов',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT category_name_english
   FROM training.wf_16
   GROUP BY category_name_english
   HAVING abs(sum(revenue_share_pct)-100)>0.02
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 17, 2, 'Первый месяц не имеет предыдущего',
 $q$SELECT to_jsonb(
   (SELECT previous_revenue IS NULL FROM training.wf_17 ORDER BY month LIMIT 1)
 )$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 20, 2, 'Первое и последнее значение стабильно в году',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT year_num FROM training.wf_20 GROUP BY year_num
   HAVING count(DISTINCT first_revenue)>1 OR count(DISTINCT last_revenue)>1
 ))$q$, $q$SELECT 'true'::jsonb$q$);

INSERT INTO training.task_tests
    (module_name, task_no, test_no, test_name, actual_sql, expected_sql)
VALUES
('window_functions', 12, 2, 'Накопление начинается заново каждый год',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM (
     SELECT year_num,min(revenue_running) first_running,min(daily_revenue) first_daily
     FROM training.wf_12 GROUP BY year_num
   ) x WHERE first_running<first_daily
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 13, 2, 'Frame содержит не более семи строк-дней',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM training.wf_13 WHERE frame_rows NOT BETWEEN 1 AND 7 OR moving_avg_7_rows IS NULL
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 14, 2, 'Календарное окно ограничено семью днями',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM training.wf_14 WHERE calendar_days_in_frame NOT BETWEEN 1 AND 7 OR moving_avg_7_days IS NULL
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 18, 2, 'Изменения месяца соответствуют формулам',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM training.wf_18
   WHERE previous_revenue IS NOT NULL AND (
     absolute_change IS DISTINCT FROM revenue-previous_revenue OR
     (previous_revenue<>0 AND abs(percent_change-100*(revenue-previous_revenue)/previous_revenue)>0.01)
   )
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 19, 2, 'Running maximum не уменьшается',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM (
     SELECT running_max,lag(running_max) OVER(ORDER BY month) previous_max
     FROM training.wf_19
   ) x WHERE running_max<previous_max
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 21, 2, 'NTILE создаёт четыре допустимые группы',
 $q$SELECT to_jsonb(
   (SELECT min(ltv_quartile)=1 AND max(ltv_quartile)=4 FROM training.wf_21)
   AND (SELECT count(*)=count(DISTINCT customer_unique_id) FROM training.wf_21)
 )$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 22, 2, 'Percent rank находится в диапазоне',
 $q$SELECT to_jsonb(
   (SELECT min(ltv_percent_rank)=0 AND max(ltv_percent_rank)<=1 FROM training.wf_22)
   AND (SELECT count(*)=count(DISTINCT customer_unique_id) FROM training.wf_22)
 )$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 23, 2, 'Cume dist монотонна и заканчивается единицей',
 $q$SELECT to_jsonb(
   (SELECT min(revenue_cume_dist)>0 AND max(revenue_cume_dist)=1 FROM training.wf_23)
   AND NOT EXISTS (
     SELECT 1 FROM (
       SELECT revenue_cume_dist,lag(revenue_cume_dist) OVER(ORDER BY revenue) previous_value
       FROM training.wf_23
     ) x WHERE revenue_cume_dist<previous_value
   )
 )$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 24, 2, 'Медиана рассчитана для каждого типа оплаты',
 $q$SELECT to_jsonb(
   (SELECT count(*)=count(DISTINCT payment_type) FROM training.wf_24)
   AND (SELECT bool_and(median_payment>=0) FROM training.wf_24)
 )$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 25, 2, 'Острова дат имеют непрерывную длину',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM training.wf_25
   WHERE island_start>island_end OR days_count<>island_end-island_start+1
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 26, 2, 'Номера сессий непрерывны внутри клиента',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM (
     SELECT customer_unique_id,min(session_no) lo,max(session_no) hi,count(DISTINCT session_no) n
     FROM training.wf_26 GROUP BY customer_unique_id
   ) x WHERE lo<>1 OR hi<>n
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 27, 2, 'Флаг повторной покупки определён один раз на клиента',
 $q$SELECT to_jsonb(
   (SELECT count(*)=count(DISTINCT customer_unique_id) FROM training.wf_27)
   AND (SELECT bool_and(repeat_within_30_days IS NOT NULL) FROM training.wf_27)
 )$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 28, 2, 'Cohort и номер месяца согласованы',
 $q$SELECT to_jsonb(NOT EXISTS (
   SELECT 1 FROM training.wf_28
   WHERE month_number<0 OR order_month<cohort_month
 ))$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 29, 2, 'Retention имеет уникальный grain и диапазон',
 $q$SELECT to_jsonb(
   (SELECT count(*)=count(DISTINCT (cohort_month,month_number)) FROM training.wf_29)
   AND (SELECT bool_and(retention_pct BETWEEN 0 AND 100) FROM training.wf_29)
 )$q$, $q$SELECT 'true'::jsonb$q$),
('window_functions', 30, 2, 'ABC-классы и накопительная доля корректны',
 $q$SELECT to_jsonb(
   (SELECT min(cumulative_share)>0 AND max(cumulative_share)>=0.999 FROM training.wf_30)
   AND (SELECT bool_and(abc_class IN ('A','B','C')) FROM training.wf_30)
   AND NOT EXISTS (
     SELECT 1 FROM (
       SELECT cumulative_share,lag(cumulative_share) OVER(ORDER BY revenue DESC,product_id) previous_share
       FROM training.wf_30
     ) x WHERE cumulative_share<previous_share
   )
 )$q$, $q$SELECT 'true'::jsonb$q$);
