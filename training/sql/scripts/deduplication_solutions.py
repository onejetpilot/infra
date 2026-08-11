"""Эталонные решения курса по дедупликации."""
SOLUTIONS={
1:("""CREATE OR REPLACE VIEW training.dq_01 AS
SELECT customer_unique_id,count(*) AS rows_count FROM staging.customers
GROUP BY customer_unique_id HAVING count(*)>1;""","Группируем по бизнес-ключу и оставляем только группы, в которых больше одной строки."),
2:("""CREATE OR REPLACE VIEW training.dq_02 AS
SELECT order_id,count(*) AS rows_count FROM raw.orders GROUP BY order_id HAVING count(*)>1;""","Считаем повторы ключа заказа в сыром слое; пустой результат тоже является корректной диагностикой."),
3:("""CREATE OR REPLACE VIEW training.dq_03 AS SELECT DISTINCT state FROM staging.customers;""","DISTINCT возвращает каждое значение штата один раз."),
4:("""CREATE OR REPLACE VIEW training.dq_04 AS
SELECT DISTINCT ON(zip_code_prefix,city) * FROM staging.geolocation
ORDER BY zip_code_prefix,city,latitude,longitude;""","DISTINCT ON задаёт составной ключ, а полный ORDER BY делает выбор строки повторяемым."),
5:("""CREATE OR REPLACE VIEW training.dq_05 AS
SELECT DISTINCT ON(customer_unique_id) * FROM staging.customers
ORDER BY customer_unique_id,customer_id;""","Внутри каждого постоянного клиента первой становится строка с минимальным customer_id."),
6:("""CREATE OR REPLACE VIEW training.dq_06 AS
SELECT c.*,row_number() OVER(PARTITION BY customer_unique_id ORDER BY customer_id) AS rn
FROM staging.customers c;""","ROW_NUMBER нумерует все версии клиента в детерминированном порядке."),
7:("""CREATE OR REPLACE VIEW training.dq_07 AS
SELECT * FROM(SELECT c.*,row_number() OVER(PARTITION BY customer_unique_id ORDER BY customer_id) rn
FROM staging.customers c)x WHERE rn>1;""","Номер рассчитываем во внутреннем запросе, а снаружи оставляем только лишние версии."),
8:("""CREATE OR REPLACE VIEW training.dq_08 AS
SELECT DISTINCT ON(order_id) * FROM staging.order_payments
ORDER BY order_id,payment_value DESC,payment_sequence;""","Максимальный платёж ставим первым, а sequence используем для разрешения ничьей."),
9:("""CREATE OR REPLACE VIEW training.dq_09 AS
SELECT DISTINCT ON(order_id,product_id) * FROM staging.order_items
ORDER BY order_id,product_id,order_item_id;""","Составной ключ — заказ и товар; минимальный номер позиции определяет победителя."),
10:("""CREATE OR REPLACE VIEW training.dq_10 AS
SELECT DISTINCT ON(order_id) * FROM staging.order_reviews
ORDER BY order_id,answered_at DESC NULLS LAST,review_id;""","Ставим самый поздний непустой timestamp первым и добавляем review_id как tie-breaker."),
11:("""CREATE OR REPLACE VIEW training.dq_11 AS
SELECT business_key,value,updated_at,is_deleted,source,count(*) rows_count
FROM training.duplicate_lab GROUP BY business_key,value,updated_at,is_deleted,source HAVING count(*)>1;""","Группируем по всем бизнес-полям, исключая технический ingest_id."),
12:("""CREATE OR REPLACE VIEW training.dq_12 AS
SELECT DISTINCT business_key,value,updated_at,is_deleted,source FROM training.duplicate_lab;""","DISTINCT удаляет только полностью одинаковые бизнес-версии."),
13:("""CREATE OR REPLACE VIEW training.dq_13 AS
SELECT DISTINCT ON(business_key) * FROM training.duplicate_lab
ORDER BY business_key,updated_at DESC,ingest_id DESC;""","Последняя дата побеждает, а больший ingest_id разрешает одинаковое время."),
14:("""CREATE OR REPLACE VIEW training.dq_14 AS
SELECT DISTINCT ON(business_key) * FROM training.duplicate_lab ORDER BY business_key,ingest_id;""","Минимальный ingest_id реализует правило first-write-wins."),
15:("""CREATE OR REPLACE VIEW training.dq_15 AS
SELECT DISTINCT ON(business_key) * FROM training.duplicate_lab
ORDER BY business_key,(value IS NULL),updated_at DESC,ingest_id DESC;""","Сначала предпочитаем непустое значение, затем наиболее свежую версию."),
16:("""CREATE OR REPLACE VIEW training.dq_16 AS
SELECT business_key,count(DISTINCT value) FILTER(WHERE value IS NOT NULL) distinct_values_count
FROM training.duplicate_lab GROUP BY business_key
HAVING count(DISTINCT value) FILTER(WHERE value IS NOT NULL)>1;""","Считаем разные непустые значения и оставляем только конфликтующие ключи."),
17:("""CREATE OR REPLACE VIEW training.dq_17 AS
SELECT business_key,count(*) versions_count,min(updated_at) first_updated_at,max(updated_at) last_updated_at
FROM training.duplicate_lab GROUP BY business_key;""","На одной группировке считаем количество версий и границы истории."),
18:("""CREATE OR REPLACE VIEW training.dq_18 AS
SELECT count(*) total_rows,count(DISTINCT (business_key,value,updated_at,is_deleted,source)) distinct_rows
FROM training.duplicate_lab;""","Сопоставляем физическое число строк с количеством разных бизнес-строк."),
19:("""CREATE OR REPLACE VIEW training.dq_19 AS
SELECT round(100.0*(count(*)-count(DISTINCT business_key))/count(*),2) duplicate_pct
FROM training.duplicate_lab;""","Лишние строки — общее количество минус уникальные ключи; делим их на весь набор."),
20:("""CREATE OR REPLACE VIEW training.dq_20 AS
WITH x AS(SELECT *,max(updated_at)OVER(PARTITION BY business_key) mx FROM training.duplicate_lab)
SELECT business_key,count(*) latest_rows_count FROM x WHERE updated_at=mx GROUP BY business_key HAVING count(*)>1;""","Оконным максимумом помечаем последние версии и находим ключи, у которых таких строк несколько."),
21:("""CREATE OR REPLACE VIEW training.dq_21 AS
SELECT DISTINCT ON(customer_unique_id) * FROM staging.customers
ORDER BY customer_unique_id,((city IS NOT NULL)::int+(state IS NOT NULL)::int) DESC,customer_id;""","Сортируем версии по числу заполненных важных полей и только затем по минимальному id."),
22:("""CREATE OR REPLACE VIEW training.dq_22 AS
WITH f AS(SELECT zip_code_prefix,latitude,longitude,count(*) freq FROM staging.geolocation GROUP BY 1,2,3)
SELECT DISTINCT ON(zip_code_prefix) zip_code_prefix,latitude,longitude FROM f
ORDER BY zip_code_prefix,freq DESC,latitude,longitude;""","Сначала считаем частоту координат, затем выбираем наиболее частую пару каждого zip-кода."),
23:("""CREATE OR REPLACE VIEW training.dq_23 AS
SELECT DISTINCT ON(product_id) * FROM staging.products
ORDER BY product_id,((product_category_name IS NOT NULL)::int+(weight_g IS NOT NULL)::int+
(length_cm IS NOT NULL)::int+(height_cm IS NOT NULL)::int+(width_cm IS NOT NULL)::int) DESC;""","Оценка качества равна числу заполненных атрибутов; первой становится наиболее полная строка."),
24:("""CREATE OR REPLACE VIEW training.dq_24 AS
SELECT * FROM(SELECT p.*,sum(payment_value)OVER(PARTITION BY order_id) total_payment_value,
row_number()OVER(PARTITION BY order_id ORDER BY payment_value DESC,payment_sequence)rn
FROM staging.order_payments p)x WHERE rn=1;""","В одном оконном проходе считаем итог заказа и номер канонического максимального платежа."),
25:("""CREATE OR REPLACE VIEW training.dq_25 AS
SELECT order_id,review_score,lower(trim(coalesce(review_message,''))) normalized_message,count(*) rows_count
FROM staging.order_reviews GROUP BY 1,2,3 HAVING count(*)>1;""","Нормализуем текст до группировки и возвращаем только повторяющиеся группы."),
26:("""CREATE OR REPLACE VIEW training.dq_26 AS
SELECT ingest_id,first_value(ingest_id)OVER(PARTITION BY business_key ORDER BY updated_at DESC,ingest_id DESC) canonical_ingest_id
FROM training.duplicate_lab;""","FIRST_VALUE назначает каждой версии id последней канонической строки её ключа."),
27:("""CREATE OR REPLACE VIEW training.dq_27 AS
SELECT business_key,array_agg(ingest_id ORDER BY ingest_id) ingest_ids FROM training.duplicate_lab GROUP BY business_key;""","Массив сохраняет происхождение и порядок всех физических версий ключа."),
28:("""CREATE OR REPLACE VIEW training.dq_28 AS
SELECT * FROM(SELECT DISTINCT ON(business_key) * FROM training.duplicate_lab
ORDER BY business_key,updated_at DESC,ingest_id DESC)x WHERE NOT is_deleted;""","Сначала выбираем последнюю версию, затем применяем tombstone, иначе удалённая сущность могла бы вернуться."),
29:("""CREATE OR REPLACE VIEW training.dq_29 AS
SELECT d.* FROM training.duplicate_lab d CROSS JOIN training.dedup_watermark w
WHERE w.pipeline_name='duplicate_lab'
  AND (d.updated_at>w.last_updated_at OR d.ingest_id>w.last_ingest_id);""","Проверяем обе границы: новая дата даёт обычный инкремент, а больший ingest_id сохраняет поздно пришедшие строки со старой бизнес-датой."),
30:("""CREATE OR REPLACE VIEW training.dq_30 AS
WITH m AS(SELECT count(*) total_rows,count(DISTINCT business_key) unique_keys FROM training.duplicate_lab),
c AS(SELECT count(*) conflict_keys FROM(SELECT business_key FROM training.duplicate_lab
GROUP BY business_key HAVING count(DISTINCT value)FILTER(WHERE value IS NOT NULL)>1)x)
SELECT total_rows,unique_keys,total_rows-unique_keys duplicate_rows,conflict_keys,
round(100.0*(total_rows-unique_keys)/total_rows,2) duplicate_pct FROM m CROSS JOIN c;""","Собираем объём, уникальные ключи и конфликты отдельно, затем вычисляем производные показатели одной строкой."),
}
