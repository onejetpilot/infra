"""Эталонные решения модуля SQL ETL."""
SOLUTIONS={
1:("""CREATE OR REPLACE VIEW training.et_01 AS SELECT
nullif(trim(order_id),'')order_id,nullif(trim(customer_id),'')customer_id,
lower(nullif(trim(order_status),''))order_status,
nullif(trim(order_purchase_timestamp),'')::timestamp purchased_at
FROM raw.orders;""","Явно очищаем текст и приводим timestamp; VIEW остаётся воспроизводимым staging-преобразованием."),
2:("""CREATE OR REPLACE VIEW training.et_02 AS SELECT *,
CASE WHEN order_purchase_timestamp~'^\\d{4}-\\d{2}-\\d{2}([ T]\\d{2}:\\d{2}:\\d{2})?$'
THEN order_purchase_timestamp::timestamp END purchased_at,
NOT(order_purchase_timestamp~'^\\d{4}-\\d{2}-\\d{2}([ T]\\d{2}:\\d{2}:\\d{2})?$')invalid_date
FROM raw.orders;""","Сначала валидируем форму регулярным выражением и только допустимые строки приводим к timestamp."),
3:("""CREATE OR REPLACE VIEW training.et_03 AS SELECT
nullif(trim(order_id),'')order_id,nullif(trim(customer_id),'')customer_id,
nullif(lower(trim(order_status)),'')order_status,nullif(trim(order_purchase_timestamp),'')purchase_text
FROM raw.orders;""","NULLIF превращает пустые после trim значения в SQL NULL, сохраняя единый смысл отсутствия."),
4:("""CREATE OR REPLACE VIEW training.et_04 AS SELECT s.*,clock_timestamp()load_dttm,
'raw.orders'::text source_name,md5(concat_ws('|',order_id,customer_id,order_status,purchased_at::text))source_hash
FROM staging.orders s;""","Добавляем происхождение, время загрузки и детерминированный hash содержательных полей."),
5:("""CREATE OR REPLACE VIEW training.et_05 AS SELECT
(SELECT count(*)FROM raw.orders)raw_rows,(SELECT count(*)FROM staging.orders)staging_rows,
(SELECT count(*)FROM raw.orders)=(SELECT count(*)FROM staging.orders)rows_match;""","Reconciliation сравнивает количество прочитанных и принятых строк отдельной контрольной записью."),
6:("""CREATE OR REPLACE VIEW training.et_06 AS SELECT
count(*)total_rows,count(*)FILTER(WHERE order_id IS NULL OR customer_id IS NULL)invalid_required_rows
FROM training.et_01;""","FILTER считает нарушения обязательных ключей, не удаляя их молча."),
7:("""CREATE OR REPLACE VIEW training.et_07 AS SELECT order_id,count(*)rows_count
FROM training.et_01 GROUP BY order_id HAVING count(*)>1 OR order_id IS NULL;""","Перед загрузкой PK отдельно выявляем дубли и NULL бизнес-ключа."),
8:("""INSERT INTO training.etl_orders(order_id,customer_id,order_status,purchased_at,source_hash)
SELECT order_id,customer_id,order_status,purchased_at,
md5(concat_ws('|',order_id,customer_id,order_status,purchased_at::text)) FROM staging.orders s
WHERE NOT EXISTS(SELECT 1 FROM training.etl_orders t WHERE t.order_id=s.order_id);
CREATE OR REPLACE VIEW training.et_08 AS SELECT * FROM training.etl_orders;""","Антисоединение вставляет только отсутствующие ключи; повтор не создаёт строки."),
9:("""INSERT INTO training.etl_orders(order_id,customer_id,order_status,purchased_at,source_hash)
SELECT order_id,customer_id,order_status,purchased_at,
md5(concat_ws('|',order_id,customer_id,order_status,purchased_at::text)) FROM staging.orders
ON CONFLICT(order_id)DO UPDATE SET customer_id=excluded.customer_id,order_status=excluded.order_status,
purchased_at=excluded.purchased_at,source_hash=excluded.source_hash,load_dttm=clock_timestamp();
CREATE OR REPLACE VIEW training.et_09 AS SELECT * FROM training.etl_orders;""","ON CONFLICT превращает загрузку в UPSERT по бизнес-ключу order_id."),
10:("""INSERT INTO training.etl_orders(order_id,customer_id,order_status,purchased_at,source_hash)
SELECT order_id,customer_id,order_status,purchased_at,
md5(concat_ws('|',order_id,customer_id,order_status,purchased_at::text)) FROM staging.orders
ON CONFLICT(order_id)DO UPDATE SET customer_id=excluded.customer_id,order_status=excluded.order_status,
purchased_at=excluded.purchased_at,source_hash=excluded.source_hash,load_dttm=clock_timestamp()
WHERE training.etl_orders.source_hash IS DISTINCT FROM excluded.source_hash;
CREATE OR REPLACE VIEW training.et_10 AS SELECT * FROM training.etl_orders;""","Условие DO UPDATE меняет только строки с отличающимся hash и не трогает load_dttm неизменных записей."),
11:("""INSERT INTO training.etl_orders(order_id,customer_id,order_status,purchased_at,source_hash)
SELECT order_id,customer_id,order_status,purchased_at,md5(concat_ws('|',order_id,customer_id,order_status,purchased_at::text))
FROM staging.orders ON CONFLICT(order_id)DO NOTHING;
CREATE OR REPLACE VIEW training.et_11 AS SELECT count(*)rows_count,count(DISTINCT order_id)unique_keys,
count(*)=count(DISTINCT order_id)idempotent_state FROM training.etl_orders;""","Повторная вставка игнорирует существующие ключи; равенство counts доказывает отсутствие дублей."),
12:("""INSERT INTO training.etl_watermark(pipeline_name,last_event_at)
SELECT 'orders_by_time',max(purchased_at)FROM training.etl_orders
ON CONFLICT(pipeline_name)DO UPDATE SET last_event_at=excluded.last_event_at,updated_at=clock_timestamp();
CREATE OR REPLACE VIEW training.et_12 AS SELECT s.* FROM staging.orders s
JOIN training.etl_watermark w ON w.pipeline_name='orders_by_time' WHERE s.purchased_at>w.last_event_at;""","Watermark хранит последнюю успешно опубликованную дату; следующий инкремент читает только более новые события."),
13:("""INSERT INTO training.etl_watermark(pipeline_name,last_id)
SELECT 'orders_by_id',max(order_id)FROM training.etl_orders
ON CONFLICT(pipeline_name)DO UPDATE SET last_id=excluded.last_id,updated_at=clock_timestamp();
CREATE OR REPLACE VIEW training.et_13 AS SELECT s.* FROM staging.orders s
JOIN training.etl_watermark w ON w.pipeline_name='orders_by_id' WHERE s.order_id>w.last_id;""","Технический watermark по ключу применим только при согласованном монотонном порядке; здесь лексикографическое правило явно зафиксировано."),
14:("""CREATE OR REPLACE VIEW training.et_14 AS SELECT s.* FROM staging.orders s
JOIN training.etl_watermark w ON w.pipeline_name='orders_by_time'
WHERE s.purchased_at>=w.last_event_at-interval '2 days';""","Overlap-окно повторно читает небольшой хвост и позволяет UPSERT поймать опоздавшие события."),
15:("""DELETE FROM training.etl_orders WHERE purchased_at>=timestamp '2018-01-01' AND purchased_at<timestamp '2018-02-01';
INSERT INTO training.etl_orders(order_id,customer_id,order_status,purchased_at,source_hash)
SELECT order_id,customer_id,order_status,purchased_at,md5(concat_ws('|',order_id,customer_id,order_status,purchased_at::text))
FROM staging.orders WHERE purchased_at>=timestamp '2018-01-01' AND purchased_at<timestamp '2018-02-01';
CREATE OR REPLACE VIEW training.et_15 AS SELECT * FROM training.etl_orders
WHERE purchased_at>=timestamp '2018-01-01' AND purchased_at<timestamp '2018-02-01';""","Delete+insert использует один полуинтервал периода, поэтому январь можно полностью переобработать без дублей."),
16:("""MERGE INTO training.etl_orders t USING(
SELECT order_id,customer_id,order_status,purchased_at,md5(concat_ws('|',order_id,customer_id,order_status,purchased_at::text))source_hash
FROM staging.orders)s ON t.order_id=s.order_id
WHEN MATCHED AND t.source_hash IS DISTINCT FROM s.source_hash THEN UPDATE SET
customer_id=s.customer_id,order_status=s.order_status,purchased_at=s.purchased_at,source_hash=s.source_hash,load_dttm=clock_timestamp()
WHEN NOT MATCHED THEN INSERT(order_id,customer_id,order_status,purchased_at,source_hash)
VALUES(s.order_id,s.customer_id,s.order_status,s.purchased_at,s.source_hash);
CREATE OR REPLACE VIEW training.et_16 AS SELECT * FROM training.etl_orders;""","MERGE разделяет изменившиеся и новые ключи; неизменные строки не обновляются."),
17:("""INSERT INTO training.etl_runs(pipeline_name,status,rows_read,rows_written,rows_rejected,finished_at)
SELECT 'orders_etl','success',(SELECT count(*)FROM raw.orders),(SELECT count(*)FROM training.etl_orders),0,clock_timestamp();
CREATE OR REPLACE VIEW training.et_17 AS SELECT * FROM training.etl_runs ORDER BY run_id DESC;""","Журнал сохраняет границы и измерения запуска отдельно от целевых данных."),
18:("""CREATE OR REPLACE VIEW training.et_18 AS SELECT run_id,pipeline_name,status,rows_read,rows_written,rows_rejected,
error_message,started_at,finished_at,finished_at-started_at duration FROM training.etl_runs;""","Единый status и error_message позволяют отличить успешный, выполняющийся и упавший запуск."),
19:("""CREATE OR REPLACE VIEW training.et_19 AS SELECT
(SELECT count(*)FROM training.etl_orders)target_rows,
(SELECT count(*)FROM training.etl_runs WHERE status='success')successful_runs,
NOT EXISTS(SELECT 1 FROM training.etl_orders WHERE order_id IS NULL)target_invariant;""","Публикация данных и фиксация success должны находиться в одной транзакции; VIEW показывает проверяемые постусловия."),
20:("""CREATE TABLE IF NOT EXISTS training.etl_orders_stage(LIKE training.etl_orders INCLUDING ALL);
TRUNCATE training.etl_orders_stage;
INSERT INTO training.etl_orders_stage(order_id,customer_id,order_status,purchased_at,source_hash)
SELECT order_id,customer_id,order_status,purchased_at,md5(concat_ws('|',order_id,customer_id,order_status,purchased_at::text))FROM staging.orders;
CREATE OR REPLACE VIEW training.et_20 AS SELECT * FROM training.etl_orders_stage;""","Полный результат сначала строится в отдельной staging-таблице и проверяется до короткой транзакции публикации."),
21:("""CREATE OR REPLACE VIEW training.et_21 AS SELECT
(SELECT sum(hashtextextended(concat_ws('|',order_id,customer_id,order_status,purchased_at::text),0)::numeric)FROM staging.orders)source_checksum,
(SELECT sum(hashtextextended(concat_ws('|',order_id,customer_id,order_status,purchased_at::text),0)::numeric)FROM training.etl_orders)target_checksum;""","Одинаковая каноническая строка и hash-функция позволяют быстро сверить содержимое двух наборов."),
22:("""CREATE OR REPLACE VIEW training.et_22 AS SELECT
(SELECT count(*)FROM staging.orders)source_rows,(SELECT count(*)FROM training.etl_orders)target_rows,
(SELECT count(*)FROM staging.orders s WHERE NOT EXISTS(SELECT 1 FROM training.etl_orders t WHERE t.order_id=s.order_id))missing_in_target,
(SELECT count(*)FROM training.etl_orders t WHERE NOT EXISTS(SELECT 1 FROM staging.orders s WHERE s.order_id=t.order_id))extra_in_target;""","Сверяем объём и оба направления отсутствующих бизнес-ключей, а не только count."),
23:("""INSERT INTO training.etl_rejects(source_name,business_key,raw_payload,reason)
SELECT 'raw.orders',order_id,to_jsonb(r),'missing key or invalid purchase timestamp' FROM raw.orders r
WHERE nullif(trim(order_id),'')IS NULL OR order_purchase_timestamp!~'^\\d{4}-\\d{2}-\\d{2}';
CREATE OR REPLACE VIEW training.et_23 AS SELECT * FROM training.etl_rejects WHERE source_name='raw.orders';""","Невалидные строки сохраняем вместе с исходным payload и причиной, а не теряем фильтром."),
24:("""UPDATE training.etl_rejects SET processed_at=clock_timestamp()
WHERE source_name='raw.orders' AND processed_at IS NULL
AND nullif(trim(business_key),'')IS NOT NULL;
CREATE OR REPLACE VIEW training.et_24 AS SELECT reject_id,business_key,reason,processed_at,
processed_at IS NOT NULL reprocessed FROM training.etl_rejects;""","Повторная обработка имеет явный статус и не удаляет исходное доказательство ошибки."),
25:("""CREATE TABLE IF NOT EXISTS training.dim_customer_scd1(
customer_unique_id text PRIMARY KEY,city text,state text,updated_at timestamptz DEFAULT clock_timestamp());
INSERT INTO training.dim_customer_scd1(customer_unique_id,city,state)
SELECT DISTINCT ON(customer_unique_id)customer_unique_id,city,state FROM staging.customers ORDER BY customer_unique_id,customer_id
ON CONFLICT(customer_unique_id)DO UPDATE SET city=excluded.city,state=excluded.state,updated_at=clock_timestamp()
WHERE (training.dim_customer_scd1.city,training.dim_customer_scd1.state)IS DISTINCT FROM(excluded.city,excluded.state);
CREATE OR REPLACE VIEW training.et_25 AS SELECT * FROM training.dim_customer_scd1;""","SCD1 хранит одну строку бизнес-ключа и перезаписывает только изменившиеся атрибуты."),
26:("""CREATE TABLE IF NOT EXISTS training.dim_customer_scd2(
customer_sk bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,customer_unique_id text NOT NULL,city text,state text,
valid_from timestamptz NOT NULL,valid_to timestamptz,is_current boolean NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_customer_scd2_current ON training.dim_customer_scd2(customer_unique_id)WHERE is_current;
INSERT INTO training.dim_customer_scd2(customer_unique_id,city,state,valid_from,is_current)
SELECT DISTINCT ON(c.customer_unique_id)c.customer_unique_id,c.city,c.state,clock_timestamp(),true FROM staging.customers c
WHERE NOT EXISTS(SELECT 1 FROM training.dim_customer_scd2 d WHERE d.customer_unique_id=c.customer_unique_id AND d.is_current)
ORDER BY c.customer_unique_id,c.customer_id;
CREATE OR REPLACE VIEW training.et_26 AS SELECT * FROM training.dim_customer_scd2;""","SCD2 отделяет surrogate key от business key и разрешает ровно одну текущую версию partial unique index."),
27:("""CREATE OR REPLACE VIEW training.et_27 AS WITH ranked AS(
SELECT *,row_number()OVER(PARTITION BY business_key ORDER BY updated_at DESC,ingest_id DESC)rn
FROM training.duplicate_lab)
SELECT * FROM ranked WHERE rn=1;""","CDC сначала дедуплицируется по business key, времени события и техническому tie-breaker."),
28:("""CREATE OR REPLACE VIEW training.et_28 AS WITH latest AS(
SELECT DISTINCT ON(business_key)* FROM training.duplicate_lab ORDER BY business_key,updated_at DESC,ingest_id DESC)
SELECT * FROM latest WHERE NOT is_deleted;""","Tombstone применяется после выбора последней версии, иначе удалённый ключ мог бы восстановиться из истории."),
29:("""CREATE TABLE IF NOT EXISTS training.etl_monthly_sales(
month date PRIMARY KEY,orders_count bigint,revenue numeric,updated_at timestamptz DEFAULT clock_timestamp());
INSERT INTO training.etl_monthly_sales(month,orders_count,revenue)
SELECT month,orders_count,revenue FROM mart.monthly_sales
ON CONFLICT(month)DO UPDATE SET orders_count=excluded.orders_count,revenue=excluded.revenue,updated_at=clock_timestamp()
WHERE (training.etl_monthly_sales.orders_count,training.etl_monthly_sales.revenue)
IS DISTINCT FROM(excluded.orders_count,excluded.revenue);
CREATE OR REPLACE VIEW training.et_29 AS SELECT * FROM training.etl_monthly_sales;""","Агрегат публикуется UPSERT по месяцу и обновляет только изменившиеся периоды."),
30:("""CREATE OR REPLACE PROCEDURE training.run_orders_etl()
LANGUAGE plpgsql AS $$ DECLARE v_run bigint;v_rows bigint;BEGIN
INSERT INTO training.etl_runs(pipeline_name,status,started_at)VALUES('orders_pipeline','running',clock_timestamp())RETURNING run_id INTO v_run;
INSERT INTO training.etl_orders(order_id,customer_id,order_status,purchased_at,source_hash)
SELECT order_id,customer_id,order_status,purchased_at,md5(concat_ws('|',order_id,customer_id,order_status,purchased_at::text))FROM staging.orders
ON CONFLICT(order_id)DO UPDATE SET customer_id=excluded.customer_id,order_status=excluded.order_status,
purchased_at=excluded.purchased_at,source_hash=excluded.source_hash WHERE training.etl_orders.source_hash IS DISTINCT FROM excluded.source_hash;
GET DIAGNOSTICS v_rows=ROW_COUNT;
UPDATE training.etl_runs SET status='success',rows_read=(SELECT count(*)FROM staging.orders),rows_written=v_rows,rows_rejected=0,finished_at=clock_timestamp()WHERE run_id=v_run;
EXCEPTION WHEN OTHERS THEN RAISE;END $$;
CALL training.run_orders_etl();
CREATE OR REPLACE VIEW training.et_30 AS SELECT * FROM training.etl_runs WHERE pipeline_name='orders_pipeline' ORDER BY run_id DESC;""","Процедура объединяет журнал, идемпотентный UPSERT и success в одну транзакцию; ошибка откатывает весь запуск."),
}
