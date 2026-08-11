"""Эталонные решения курса по оконным функциям."""
SOLUTIONS={
1:("""CREATE OR REPLACE VIEW training.wf_01 AS SELECT order_id,purchased_at,
row_number()OVER(ORDER BY purchased_at,order_id) row_num FROM staging.orders;""","Глобальный порядок задают время и ключ заказа; ROW_NUMBER выдаёт непрерывные номера."),
2:("""CREATE OR REPLACE VIEW training.wf_02 AS SELECT order_id,order_status,purchased_at,
row_number()OVER(PARTITION BY order_status ORDER BY purchased_at,order_id) row_num FROM staging.orders;""","PARTITION BY начинает нумерацию заново для каждого статуса."),
3:("""CREATE OR REPLACE VIEW training.wf_03 AS SELECT order_id,payment_value,
dense_rank()OVER(ORDER BY payment_value DESC) payment_rank FROM mart.order_finance;""","DENSE_RANK присваивает одинаковым суммам один ранг и не оставляет пропусков."),
4:("""CREATE OR REPLACE VIEW training.wf_04 AS SELECT order_id,payment_value,
row_number()OVER(ORDER BY payment_value DESC,order_id) row_num,
rank()OVER(ORDER BY payment_value DESC) payment_rank,
dense_rank()OVER(ORDER BY payment_value DESC) dense_payment_rank FROM mart.order_finance;""","Три функции получают одинаковое направление суммы; tie-breaker нужен только уникальному ROW_NUMBER."),
5:("""CREATE OR REPLACE VIEW training.wf_05 AS WITH x AS(
SELECT c.state,o.order_id,f.payment_value,row_number()OVER(PARTITION BY c.state ORDER BY f.payment_value DESC,o.order_id)row_num
FROM staging.orders o JOIN staging.customers c USING(customer_id) JOIN mart.order_finance f USING(order_id))
SELECT * FROM x WHERE row_num<=3;""","Сначала ранжируем заказы внутри штата, затем снаружи оставляем три первых."),
6:("""CREATE OR REPLACE VIEW training.wf_06 AS WITH x AS(
SELECT customer_unique_id,order_id,purchased_at,row_number()OVER(PARTITION BY customer_unique_id ORDER BY purchased_at,order_id)rn
FROM mart.order_finance) SELECT customer_unique_id,order_id,purchased_at FROM x WHERE rn=1;""","Первая покупка получает rn=1 внутри постоянного покупателя; готовая витрина исключает лишний JOIN."),
7:("""CREATE OR REPLACE VIEW training.wf_07 AS WITH x AS(
SELECT customer_unique_id,order_id,purchased_at,row_number()OVER(PARTITION BY customer_unique_id ORDER BY purchased_at DESC,order_id DESC)rn
FROM mart.order_finance) SELECT customer_unique_id,order_id,purchased_at FROM x WHERE rn=1;""","Обратная сортировка ставит последнюю покупку первой; customer_unique_id уже есть в витрине."),
8:("""CREATE OR REPLACE VIEW training.wf_08 AS SELECT customer_unique_id,order_id,purchased_at,
lag(purchased_at)OVER(PARTITION BY customer_unique_id ORDER BY purchased_at,order_id)previous_purchased_at
FROM mart.order_finance;""","LAG читает предыдущую покупку в упорядоченной истории клиента."),
9:("""CREATE OR REPLACE VIEW training.wf_09 AS WITH x AS(
SELECT customer_unique_id,order_id,purchased_at,lag(purchased_at)OVER(PARTITION BY customer_unique_id ORDER BY purchased_at,order_id)prev
FROM mart.order_finance)
SELECT *,purchased_at::date-prev::date days_since_previous FROM x;""","Сохраняем LAG в CTE и вычитаем календарные даты соседних покупок."),
10:("""CREATE OR REPLACE VIEW training.wf_10 AS SELECT customer_unique_id,order_id,purchased_at,
lead(purchased_at)OVER(PARTITION BY customer_unique_id ORDER BY purchased_at,order_id)next_purchased_at
FROM mart.order_finance;""","LEAD возвращает следующую строку истории; для последней покупки получается NULL."),
11:("""CREATE OR REPLACE VIEW training.wf_11 AS WITH d AS(
SELECT purchased_at::date sale_date,sum(payment_value)daily_revenue FROM mart.order_finance GROUP BY 1)
SELECT *,sum(daily_revenue)OVER(ORDER BY sale_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)revenue_running FROM d;""","Сначала получаем одну строку дня, затем явный ROWS-frame накапливает выручку."),
12:("""CREATE OR REPLACE VIEW training.wf_12 AS WITH d AS(
SELECT purchased_at::date sale_date,extract(year FROM purchased_at)::int year_num,sum(payment_value)daily_revenue FROM mart.order_finance GROUP BY 1,2)
SELECT *,sum(daily_revenue)OVER(PARTITION BY year_num ORDER BY sale_date ROWS UNBOUNDED PRECEDING)revenue_running FROM d;""","PARTITION BY year_num сбрасывает накопление в начале каждого года."),
13:("""CREATE OR REPLACE VIEW training.wf_13 AS WITH d AS(
SELECT purchased_at::date sale_date,sum(payment_value)daily_revenue FROM mart.order_finance GROUP BY 1)
SELECT *,avg(daily_revenue)OVER(ORDER BY sale_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)moving_avg_7_rows,
count(*)OVER(ORDER BY sale_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)frame_rows FROM d;""","ROWS берёт текущую и шесть физических строк-дней независимо от пропусков календаря."),
14:("""CREATE OR REPLACE VIEW training.wf_14 AS WITH bounds AS(
SELECT min(purchased_at::date)lo,max(purchased_at::date)hi FROM mart.order_finance),days AS(
SELECT generate_series(lo,hi,interval '1 day')::date sale_date FROM bounds),rev AS(
SELECT purchased_at::date sale_date,sum(payment_value)daily_revenue FROM mart.order_finance GROUP BY 1),d AS(
SELECT days.sale_date,coalesce(rev.daily_revenue,0)daily_revenue FROM days LEFT JOIN rev USING(sale_date))
SELECT *,avg(daily_revenue)OVER(ORDER BY sale_date RANGE BETWEEN interval '6 days' PRECEDING AND CURRENT ROW)moving_avg_7_days,
count(*)OVER(ORDER BY sale_date RANGE BETWEEN interval '6 days' PRECEDING AND CURRENT ROW)calendar_days_in_frame FROM d;""","Заполняем календарь нулевыми днями, после чего RANGE действительно охватывает семь календарных дат."),
15:("""CREATE OR REPLACE VIEW training.wf_15 AS SELECT *,sum(revenue)OVER(PARTITION BY category_name_english)category_revenue FROM mart.product_sales;""","Оконная сумма добавляет итог категории к каждой строке товара, не схлопывая товары."),
16:("""CREATE OR REPLACE VIEW training.wf_16 AS SELECT *,
100*revenue/nullif(sum(revenue)OVER(PARTITION BY category_name_english),0)revenue_share_pct FROM mart.product_sales;""","Делим выручку товара на оконный итог его категории; NULLIF защищает нулевой знаменатель."),
17:("""CREATE OR REPLACE VIEW training.wf_17 AS SELECT month,revenue,lag(revenue)OVER(ORDER BY month)previous_revenue FROM mart.monthly_sales;""","LAG сопоставляет месяц с непосредственно предыдущей строкой временного ряда."),
18:("""CREATE OR REPLACE VIEW training.wf_18 AS WITH x AS(
SELECT month,revenue,lag(revenue)OVER(ORDER BY month)previous_revenue FROM mart.monthly_sales)
SELECT *,revenue-previous_revenue absolute_change,
100*(revenue-previous_revenue)/nullif(previous_revenue,0)percent_change FROM x;""","Предыдущее значение считаем один раз, затем используем его в абсолютной и процентной формулах."),
19:("""CREATE OR REPLACE VIEW training.wf_19 AS SELECT month,revenue,
max(revenue)OVER(ORDER BY month ROWS UNBOUNDED PRECEDING)running_max FROM mart.monthly_sales;""","Накопительный MAX хранит лучший месячный результат, достигнутый к текущему месяцу."),
20:("""CREATE OR REPLACE VIEW training.wf_20 AS SELECT month,extract(year FROM month)::int year_num,revenue,
first_value(revenue)OVER(PARTITION BY extract(year FROM month)ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)first_revenue,
last_value(revenue)OVER(PARTITION BY extract(year FROM month)ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)last_revenue
FROM mart.monthly_sales;""","Полный frame до UNBOUNDED FOLLOWING нужен, чтобы LAST_VALUE видел конец года, а не текущую строку."),
21:("""CREATE OR REPLACE VIEW training.wf_21 AS SELECT customer_unique_id,lifetime_value,
ntile(4)OVER(ORDER BY lifetime_value DESC NULLS LAST,customer_unique_id)ltv_quartile FROM mart.customer_summary;""","NTILE делит упорядоченных покупателей на четыре максимально близкие по размеру группы."),
22:("""CREATE OR REPLACE VIEW training.wf_22 AS SELECT customer_unique_id,lifetime_value,
percent_rank()OVER(ORDER BY lifetime_value,customer_unique_id)ltv_percent_rank FROM mart.customer_summary;""","PERCENT_RANK показывает относительную позицию от нуля до единицы."),
23:("""CREATE OR REPLACE VIEW training.wf_23 AS SELECT product_id,revenue,
cume_dist()OVER(ORDER BY revenue,product_id)revenue_cume_dist FROM mart.product_sales;""","CUME_DIST возвращает накопленную долю строк с текущим или меньшим значением."),
24:("""CREATE OR REPLACE VIEW training.wf_24 AS SELECT payment_type,
percentile_cont(0.5)WITHIN GROUP(ORDER BY payment_value)median_payment FROM staging.order_payments GROUP BY payment_type;""","Ordered-set aggregate вычисляет медиану отдельно для каждого типа платежа."),
25:("""CREATE OR REPLACE VIEW training.wf_25 AS WITH dates AS(
SELECT DISTINCT purchased_at::date sale_date FROM staging.orders),marked AS(
SELECT sale_date,sale_date-row_number()OVER(ORDER BY sale_date)::int island_key FROM dates)
SELECT min(sale_date)island_start,max(sale_date)island_end,count(*)::int days_count FROM marked GROUP BY island_key;""","У последовательных дат выражение date-row_number постоянно; оно образует ключ острова."),
26:("""CREATE OR REPLACE VIEW training.wf_26 AS WITH history AS(
SELECT customer_unique_id,order_id,purchased_at,lag(purchased_at)OVER(PARTITION BY customer_unique_id ORDER BY purchased_at,order_id)prev
FROM mart.order_finance),flags AS(
SELECT *,CASE WHEN prev IS NULL OR purchased_at>prev+interval '30 days' THEN 1 ELSE 0 END new_session FROM history)
SELECT *,sum(new_session)OVER(PARTITION BY customer_unique_id ORDER BY purchased_at,order_id ROWS UNBOUNDED PRECEDING)::int session_no FROM flags;""","LAG находит разрыв, флаг отмечает начало, а накопительная сумма превращает флаги в номера сессий."),
27:("""CREATE OR REPLACE VIEW training.wf_27 AS WITH h AS(
SELECT customer_unique_id,purchased_at,min(purchased_at)OVER(PARTITION BY customer_unique_id)first_at FROM mart.order_finance)
SELECT customer_unique_id,bool_or(purchased_at>first_at AND purchased_at<=first_at+interval '30 days')repeat_within_30_days
FROM h GROUP BY customer_unique_id;""","Оконный MIN задаёт первую покупку, а BOOL_OR сворачивает историю до одного признака клиента."),
28:("""CREATE OR REPLACE VIEW training.wf_28 AS WITH h AS(
SELECT customer_unique_id,order_id,date_trunc('month',purchased_at)::date order_month,
date_trunc('month',min(purchased_at)OVER(PARTITION BY customer_unique_id))::date cohort_month FROM mart.order_finance)
SELECT *,((extract(year FROM order_month)-extract(year FROM cohort_month))*12+
extract(month FROM order_month)-extract(month FROM cohort_month))::int month_number FROM h;""","Когорта — месяц первой покупки; разность год×12+месяц даёт номер месяца жизни."),
29:("""CREATE OR REPLACE VIEW training.wf_29 AS WITH cm AS(
SELECT DISTINCT customer_unique_id,date_trunc('month',purchased_at)::date order_month,
date_trunc('month',min(purchased_at)OVER(PARTITION BY customer_unique_id))::date cohort_month FROM mart.order_finance),n AS(
SELECT *,((extract(year FROM order_month)-extract(year FROM cohort_month))*12+
extract(month FROM order_month)-extract(month FROM cohort_month))::int month_number FROM cm),sizes AS(
SELECT cohort_month,count(*)FILTER(WHERE month_number=0)::numeric cohort_size FROM n GROUP BY cohort_month)
SELECT n.cohort_month,n.month_number,count(*)customers_count,
round(100*count(*)/nullif(s.cohort_size,0),2)retention_pct FROM n JOIN sizes s USING(cohort_month)
GROUP BY n.cohort_month,n.month_number,s.cohort_size;""","Уникализируем клиент-месяц, считаем размер нулевого месяца и делим активных клиентов каждого периода на размер когорты."),
30:("""CREATE OR REPLACE VIEW training.wf_30 AS WITH r AS(
SELECT product_id,revenue,sum(revenue)OVER(ORDER BY revenue DESC,product_id ROWS UNBOUNDED PRECEDING)/nullif(sum(revenue)OVER(),0)cumulative_share
FROM mart.product_sales)
SELECT *,CASE WHEN cumulative_share<=0.8 THEN 'A' WHEN cumulative_share<=0.95 THEN 'B' ELSE 'C' END abc_class FROM r;""","Сортируем товары по выручке, считаем накопительную долю общего итога и назначаем классы порогами 80/95%."),
}
