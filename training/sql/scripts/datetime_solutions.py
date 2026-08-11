"""Эталонные решения модуля дат и временных рядов."""

SOLUTIONS = {
1: ("""CREATE OR REPLACE VIEW training.dt_01 AS
SELECT order_id,purchased_at,purchased_at::date AS purchase_date,
       purchased_at AT TIME ZONE 'America/Sao_Paulo' AS purchase_moment
FROM staging.orders;""", "Одна строка — заказ. Показываем календарную дату, локальный timestamp и абсолютный момент."),
2: ("""CREATE OR REPLACE VIEW training.dt_02 AS
SELECT order_id,purchased_at,date_trunc('day',purchased_at) AS day_start,
       date_trunc('month',purchased_at)::date AS month_start
FROM staging.orders WHERE purchased_at IS NOT NULL;""", "date_trunc обрезает младшие компоненты; grain остаётся заказом."),
3: ("""CREATE OR REPLACE VIEW training.dt_03 AS
SELECT order_id,extract(year FROM purchased_at)::int AS year_num,
       extract(month FROM purchased_at)::int AS month_num,
       extract(isodow FROM purchased_at)::int AS iso_weekday,
       extract(hour FROM purchased_at)::int AS hour_num
FROM staging.orders WHERE purchased_at IS NOT NULL;""", "Из одного timestamp получаем компоненты для календарного анализа."),
4: ("""CREATE OR REPLACE VIEW training.dt_04 AS
SELECT order_id,purchased_at,purchased_at+interval '7 days' AS plus_week,
       purchased_at+interval '1 month' AS plus_month
FROM staging.orders WHERE purchased_at IS NOT NULL;""", "Интервал хранит длительность; один месяц не равен фиксированным 30 дням."),
5: ("""CREATE OR REPLACE VIEW training.dt_05 AS
SELECT order_id,purchased_at,current_date-purchased_at::date AS age_days
FROM staging.orders WHERE purchased_at IS NOT NULL;""", "Возраст выражен целым числом календарных дней; grain — заказ."),
6: ("""CREATE OR REPLACE VIEW training.dt_06 AS
SELECT order_id,date_trunc('month',purchased_at)::date AS month_start,
       (date_trunc('month',purchased_at)+interval '1 month-1 day')::date AS month_end
FROM staging.orders WHERE purchased_at IS NOT NULL;""", "Границы месяца вычисляются от его начала и корректны для месяцев разной длины."),
7: ("""CREATE OR REPLACE VIEW training.dt_07 AS
SELECT d::date AS calendar_date
FROM generate_series((SELECT min(purchased_at)::date FROM staging.orders),
                     (SELECT max(purchased_at)::date FROM staging.orders),interval '1 day') d;""", "Одна строка — каждый календарный день между первой и последней покупкой."),
8: ("""CREATE OR REPLACE VIEW training.dt_08 AS
WITH days AS (SELECT d::date AS day FROM generate_series(
 (SELECT min(purchased_at)::date FROM staging.orders),
 (SELECT max(purchased_at)::date FROM staging.orders),interval '1 day') d),
orders_by_day AS (SELECT purchased_at::date AS day,count(*) AS orders_count
 FROM staging.orders GROUP BY 1)
SELECT d.day,coalesce(o.orders_count,0) AS orders_count
FROM days d LEFT JOIN orders_by_day o USING(day);""", "Календарь является левой стороной JOIN, поэтому дни без заказов не исчезают."),
9: ("""CREATE OR REPLACE VIEW training.dt_09 AS
SELECT purchased_at::date AS day,count(*) AS orders_count,
       sum(payment_value) AS revenue
FROM mart.order_finance
WHERE order_status NOT IN ('canceled','unavailable')
GROUP BY purchased_at::date;""", "Одна строка — торговый день; выручка считается на grain заказа."),
10: ("""CREATE OR REPLACE VIEW training.dt_10 AS
SELECT extract(isoyear FROM purchased_at)::int AS iso_year,
       extract(week FROM purchased_at)::int AS iso_week,
       date_trunc('week',purchased_at)::date AS week_start,count(*) AS orders_count
FROM staging.orders WHERE purchased_at IS NOT NULL GROUP BY 1,2,3;""", "ISO-неделю связываем с ISO-годом, иначе граница года даст неверную группу."),
11: ("""CREATE OR REPLACE VIEW training.dt_11 AS
SELECT date_trunc('month',purchased_at)::date AS month_start,
       count(*) AS orders_count,sum(payment_value) AS revenue
FROM mart.order_finance WHERE order_status NOT IN ('canceled','unavailable') GROUP BY 1;""", "Одна строка — календарный месяц; факты заказа агрегируются один раз."),
12: ("""CREATE OR REPLACE VIEW training.dt_12 AS
SELECT date_trunc('quarter',purchased_at)::date AS quarter_start,
       count(*) AS orders_count,sum(payment_value) AS revenue
FROM mart.order_finance WHERE order_status NOT IN ('canceled','unavailable') GROUP BY 1;""", "date_trunc('quarter') создаёт устойчивый ключ квартала."),
13: ("""CREATE OR REPLACE VIEW training.dt_13 AS
WITH daily AS (SELECT purchased_at::date AS day,sum(payment_value) AS revenue
 FROM mart.order_finance WHERE order_status NOT IN ('canceled','unavailable') GROUP BY 1),
calendar AS (SELECT d::date AS day FROM generate_series((SELECT min(day) FROM daily),
 (SELECT max(day) FROM daily),interval '1 day') d),
filled AS (SELECT c.day,coalesce(d.revenue,0) AS revenue FROM calendar c LEFT JOIN daily d USING(day))
SELECT day,revenue,sum(revenue) OVER(ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS revenue_7d
FROM filled;""", "Сначала заполняем пропущенные даты, затем семь строк действительно означают семь календарных дней."),
14: ("""CREATE OR REPLACE VIEW training.dt_14 AS
WITH daily AS (SELECT purchased_at::date AS day,sum(payment_value) AS revenue
 FROM mart.order_finance WHERE order_status NOT IN ('canceled','unavailable') GROUP BY 1)
SELECT day,revenue,sum(revenue) OVER(PARTITION BY date_trunc('month',day) ORDER BY day) AS revenue_mtd
FROM daily;""", "MTD накапливается заново внутри каждого месяца."),
15: ("""CREATE OR REPLACE VIEW training.dt_15 AS
WITH monthly AS (SELECT date_trunc('month',purchased_at)::date AS month,sum(payment_value) AS revenue
 FROM mart.order_finance WHERE order_status NOT IN ('canceled','unavailable') GROUP BY 1)
SELECT month,revenue,sum(revenue) OVER(PARTITION BY extract(year FROM month) ORDER BY month) AS revenue_ytd
FROM monthly;""", "YTD сбрасывается на границе календарного года; grain — месяц."),
16: ("""CREATE OR REPLACE VIEW training.dt_16 AS
SELECT month,revenue,lag(revenue) OVER(ORDER BY month) AS previous_revenue,
       revenue-lag(revenue) OVER(ORDER BY month) AS absolute_change
FROM mart.monthly_sales;""", "LAG возвращает показатель предыдущего месяца без self join."),
17: ("""CREATE OR REPLACE VIEW training.dt_17 AS
SELECT month,revenue,lag(revenue,12) OVER(ORDER BY month) AS revenue_year_ago,
       round(100*(revenue-lag(revenue,12) OVER(ORDER BY month)) /
       nullif(lag(revenue,12) OVER(ORDER BY month),0),2) AS yoy_pct
FROM mart.monthly_sales;""", "Сравниваем месяц с двенадцатой предыдущей строкой полного месячного ряда."),
18: ("""CREATE OR REPLACE VIEW training.dt_18 AS
SELECT d::date AS calendar_date,extract(isodow FROM d)::int AS iso_weekday,
       extract(isodow FROM d) BETWEEN 1 AND 5 AS is_workday
FROM generate_series(date '2016-01-01',date '2018-12-31',interval '1 day') d;""", "ISO 1–5 — понедельник–пятница; одна строка — день."),
19: ("""CREATE OR REPLACE VIEW training.dt_19 AS
WITH holidays(day,name) AS (VALUES (date '2017-01-01','New Year'),
 (date '2017-04-21','Tiradentes'),(date '2017-09-07','Independence Day'),
 (date '2017-12-25','Christmas'))
SELECT d::date AS calendar_date,h.name AS holiday_name,h.day IS NOT NULL AS is_holiday
FROM generate_series(date '2017-01-01',date '2017-12-31',interval '1 day') d
LEFT JOIN holidays h ON h.day=d::date;""", "Праздники моделируются отдельным календарным атрибутом, а не длинным CASE в факте."),
20: ("""CREATE OR REPLACE VIEW training.dt_20 AS
SELECT order_id,purchased_at,
       purchased_at AT TIME ZONE 'America/Sao_Paulo' AS purchased_timestamptz,
       (purchased_at AT TIME ZONE 'America/Sao_Paulo') AT TIME ZONE 'UTC' AS utc_time
FROM staging.orders WHERE purchased_at IS NOT NULL;""", "Исходное локальное время явно связывается с зоной São Paulo и переводится в UTC."),
21: ("""CREATE OR REPLACE VIEW training.dt_21 AS
SELECT x.local_time,x.local_time AT TIME ZONE 'America/New_York' AS absolute_time
FROM (VALUES(timestamp '2021-03-14 01:30'),(timestamp '2021-03-14 03:30'),
             (timestamp '2021-11-07 01:30')) x(local_time);""", "Контрольные моменты показывают пропуск и повтор локального часа при DST."),
22: ("""CREATE OR REPLACE VIEW training.dt_22 AS
SELECT order_id,purchased_at,delivered_to_customer_at,
       delivered_to_customer_at-purchased_at AS delivery_interval,
       delivered_to_customer_at::date-purchased_at::date AS delivery_days
FROM staging.orders WHERE delivered_to_customer_at IS NOT NULL;""", "Длительность хранится interval, а календарные дни — отдельным целым показателем."),
23: ("""CREATE OR REPLACE VIEW training.dt_23 AS
SELECT order_id,delivered_to_customer_at,estimated_delivery_at,
       delivered_to_customer_at>estimated_delivery_at AS is_late,
       greatest(delivered_to_customer_at::date-estimated_delivery_at::date,0) AS late_days
FROM staging.orders WHERE delivered_to_customer_at IS NOT NULL AND estimated_delivery_at IS NOT NULL;""", "Просрочка считается только при наличии обеих дат; отрицательное число дней заменяется нулём."),
24: ("""CREATE OR REPLACE VIEW training.dt_24 AS
SELECT date_trunc('hour',purchased_at) AS hour_start,count(*) AS orders_count
FROM staging.orders WHERE purchased_at IS NOT NULL GROUP BY 1;""", "Каждое событие попадает в часовой полуинтервал, представленный его началом."),
25: ("""CREATE OR REPLACE VIEW training.dt_25 AS
WITH days AS (SELECT DISTINCT purchased_at::date AS day FROM staging.orders),
marked AS (SELECT day,day-row_number() OVER(ORDER BY day)::int AS island_key FROM days)
SELECT min(day) AS island_start,max(day) AS island_end,count(*) AS days_count
FROM marked GROUP BY island_key;""", "Для последовательных дат разность date-row_number постоянна и образует остров."),
26: ("""CREATE OR REPLACE VIEW training.dt_26 AS
WITH activity AS (SELECT DISTINCT c.customer_unique_id,o.purchased_at::date AS day
 FROM staging.orders o JOIN staging.customers c USING(customer_id)),
marked AS (SELECT *,day-row_number() OVER(PARTITION BY customer_unique_id ORDER BY day)::int AS island_key FROM activity)
SELECT customer_unique_id,min(day) AS sequence_start,max(day) AS sequence_end,count(*) AS active_days
FROM marked GROUP BY customer_unique_id,island_key;""", "Острова рассчитываются отдельно для каждого покупателя; grain — последовательность активности."),
27: ("""CREATE OR REPLACE VIEW training.dt_27 AS
SELECT customer_unique_id,date_trunc('month',min(purchased_at))::date AS cohort_month
FROM mart.order_finance GROUP BY customer_unique_id;""", "Когорта покупателя определяется месяцем первой покупки."),
28: ("""CREATE OR REPLACE VIEW training.dt_28 AS
WITH activity AS (SELECT customer_unique_id,date_trunc('month',purchased_at)::date AS activity_month
 FROM mart.order_finance GROUP BY 1,2),
cohorts AS (SELECT customer_unique_id,min(activity_month) AS cohort_month FROM activity GROUP BY 1),
retained AS (SELECT c.cohort_month,a.activity_month,
 ((extract(year FROM a.activity_month)-extract(year FROM c.cohort_month))*12+
   extract(month FROM a.activity_month)-extract(month FROM c.cohort_month))::int AS month_no,
 count(*) AS retained_customers FROM cohorts c JOIN activity a USING(customer_unique_id) GROUP BY 1,2,3),
sizes AS (SELECT cohort_month,count(*) AS cohort_size FROM cohorts GROUP BY 1)
SELECT r.*,s.cohort_size,round(r.retained_customers::numeric/s.cohort_size,4) AS retention_rate
FROM retained r JOIN sizes s USING(cohort_month);""", "Одна строка — когорта и номер месяца; знаменатель всегда исходный размер когорты."),
29: ("""CREATE OR REPLACE VIEW training.dt_29 AS
WITH params AS (SELECT date '2018-01-01' AS snapshot_date)
SELECT p.snapshot_date,o.order_id,o.order_status,o.purchased_at,o.delivered_to_customer_at,
       CASE WHEN o.delivered_to_customer_at<p.snapshot_date THEN 'delivered' ELSE 'open' END AS state_at_date
FROM params p JOIN staging.orders o ON o.purchased_at<p.snapshot_date
WHERE o.delivered_to_customer_at IS NULL OR o.delivered_to_customer_at>=p.snapshot_date;""", "Snapshot использует только события, известные к выбранной дате, и показывает открытые тогда заказы."),
30: ("""CREATE OR REPLACE VIEW training.dt_30 AS
WITH daily AS (SELECT purchased_at::date AS day,count(*) AS orders_count,
 sum(payment_value) AS revenue,count(DISTINCT customer_unique_id) AS customers_count
 FROM mart.order_finance WHERE order_status NOT IN ('canceled','unavailable') GROUP BY 1),
calendar AS (SELECT d::date AS day FROM generate_series((SELECT min(day) FROM daily),
 (SELECT max(day) FROM daily),interval '1 day') d),
filled AS (SELECT c.day,coalesce(d.orders_count,0) AS orders_count,
 coalesce(d.revenue,0) AS revenue,coalesce(d.customers_count,0) AS customers_count
 FROM calendar c LEFT JOIN daily d USING(day))
SELECT *,sum(revenue) OVER(ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS revenue_7d,
 sum(revenue) OVER(PARTITION BY date_trunc('month',day) ORDER BY day) AS revenue_mtd,
 lag(revenue) OVER(ORDER BY day) AS previous_day_revenue
FROM filled;""", "Полная дневная витрина не теряет пустые даты и содержит базовые и оконные показатели."),
}
