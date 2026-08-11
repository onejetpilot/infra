"""Эталонные решения модуля JSONB и массивов PostgreSQL."""

SOLUTIONS = {
1: ("""CREATE OR REPLACE VIEW training.js_01 AS
SELECT order_id,jsonb_build_object('status',order_status,'purchased_at',purchased_at) AS payload
FROM staging.orders;""", "Одна строка — заказ; выбранные колонки собраны в JSONB-объект."),
2: ("""CREATE OR REPLACE VIEW training.js_02 AS
WITH src AS (SELECT order_id,jsonb_build_object('status',order_status,'customer_id',customer_id) payload FROM staging.orders)
SELECT order_id,payload->'status' AS status_json,payload->>'status' AS status_text FROM src;""", "Оператор -> сохраняет JSONB, а ->> возвращает text."),
3: ("""CREATE OR REPLACE VIEW training.js_03 AS
WITH src AS (SELECT order_id,jsonb_build_object('customer',jsonb_build_object('id',customer_id)) payload FROM staging.orders)
SELECT order_id,payload#>>'{customer,id}' AS customer_id FROM src;""", "#>> извлекает вложенное значение по массиву компонентов пути."),
4: ("""CREATE OR REPLACE VIEW training.js_04 AS
WITH src AS (SELECT order_id,jsonb_build_object('status',order_status,'approved_at',approved_at) payload FROM staging.orders)
SELECT order_id,payload ? 'approved_at' AS has_key,payload->>'approved_at' AS approved_at FROM src;""", "Оператор ? проверяет наличие ключа, даже если его JSON-значение null."),
5: ("""CREATE OR REPLACE VIEW training.js_05 AS
WITH src AS (SELECT order_id,jsonb_build_object('status',order_status,'customer_id',customer_id) payload FROM staging.orders)
SELECT order_id,payload FROM src WHERE payload @> '{\"status\":\"delivered\"}'::jsonb;""", "@> проверяет, содержит ли левый JSONB заданный фрагмент."),
6: ("""CREATE OR REPLACE VIEW training.js_06 AS
WITH src AS (SELECT order_id,jsonb_build_object('status',order_status,'customer_id',customer_id) payload FROM staging.orders)
SELECT s.order_id,e.key,e.value FROM src s CROSS JOIN LATERAL jsonb_each(s.payload) e;""", "jsonb_each превращает пары ключ-значение объекта в строки."),
7: ("""CREATE OR REPLACE VIEW training.js_07 AS
WITH src AS (SELECT order_id,jsonb_agg(jsonb_build_object('sequence',payment_sequence,'value',payment_value) ORDER BY payment_sequence) payload
 FROM staging.order_payments GROUP BY order_id)
SELECT s.order_id,e.value AS payment FROM src s CROSS JOIN LATERAL jsonb_array_elements(s.payload) e;""", "Массив платежей разворачивается обратно; grain результата — часть платежа."),
8: ("""CREATE OR REPLACE VIEW training.js_08 AS
WITH src AS (SELECT order_id,jsonb_agg(jsonb_build_object('seq',payment_sequence,'type',payment_type,'value',payment_value)) payload
 FROM staging.order_payments GROUP BY order_id)
SELECT s.order_id,x.* FROM src s CROSS JOIN LATERAL
 jsonb_to_recordset(s.payload) AS x(seq int,type text,value numeric);""", "jsonb_to_recordset сразу задаёт реляционные имена и типы полей."),
9: ("""CREATE OR REPLACE VIEW training.js_09 AS
WITH src AS (SELECT order_id,jsonb_build_object('payment',jsonb_build_object('value',payment_value)) payload FROM staging.order_payments)
SELECT order_id,payload FROM src WHERE payload @@ '$.payment.value > 1000';""", "SQL/JSON path фильтрует вложенные числовые значения без текстового сравнения."),
10: ("""CREATE OR REPLACE VIEW training.js_10 AS
WITH src AS (SELECT order_id,jsonb_build_object('status',order_status) payload FROM staging.orders)
SELECT order_id,jsonb_set(payload,'{processed}','true'::jsonb,true) AS payload FROM src;""", "jsonb_set добавляет или заменяет значение по заданному пути."),
11: ("""CREATE OR REPLACE VIEW training.js_11 AS
WITH src AS (SELECT order_id,jsonb_build_object('status',order_status,'customer_id',customer_id) payload FROM staging.orders)
SELECT order_id,payload-'customer_id' AS payload FROM src;""", "Минус с текстовым ключом удаляет поле верхнего уровня."),
12: ("""CREATE OR REPLACE VIEW training.js_12 AS
SELECT order_id,jsonb_build_object('status',order_status) ||
       jsonb_build_object('purchased_at',purchased_at,'customer_id',customer_id) AS payload
FROM staging.orders;""", "|| объединяет объекты; при совпадении ключа побеждает значение справа."),
13: ("""CREATE OR REPLACE VIEW training.js_13 AS
SELECT order_id,jsonb_agg(jsonb_build_object('item_id',order_item_id,'product_id',product_id,'price',price)
 ORDER BY order_item_id) AS items
FROM staging.order_items GROUP BY order_id;""", "Одна строка — заказ, элементы заказа собраны в упорядоченный JSON-массив."),
14: ("""CREATE OR REPLACE VIEW training.js_14 AS
SELECT order_id,jsonb_object_agg(payment_sequence::text,payment_value) AS payments_by_sequence
FROM staging.order_payments GROUP BY order_id;""", "Ключи объекта должны быть текстовыми и уникальными внутри заказа."),
15: ("""CREATE OR REPLACE VIEW training.js_15 AS
SELECT order_id,to_jsonb(approved_at) AS approved_json,
       jsonb_build_object('approved_at',approved_at)->'approved_at' AS field_value,
       approved_at IS NULL AS is_sql_null
FROM staging.orders;""", "Различаем SQL NULL, JSON null и отсутствие ключа."),
16: ("""CREATE TABLE IF NOT EXISTS training.js_documents(id text PRIMARY KEY,payload jsonb NOT NULL);
CREATE INDEX IF NOT EXISTS ix_js_documents_payload_ops ON training.js_documents USING gin(payload jsonb_ops);
CREATE OR REPLACE VIEW training.js_16 AS
SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='training' AND tablename='js_documents';""", "Обычный GIN jsonb_ops поддерживает широкий набор операторов JSONB."),
17: ("""CREATE TABLE IF NOT EXISTS training.js_path_documents(id text PRIMARY KEY,payload jsonb NOT NULL);
CREATE INDEX IF NOT EXISTS ix_js_path_documents_payload ON training.js_path_documents USING gin(payload jsonb_path_ops);
CREATE OR REPLACE VIEW training.js_17 AS
SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='training' AND tablename='js_path_documents';""", "jsonb_path_ops компактнее для containment и jsonpath, но поддерживает меньше операторов."),
18: ("""CREATE TABLE IF NOT EXISTS training.js_status_documents(id text PRIMARY KEY,payload jsonb NOT NULL);
CREATE INDEX IF NOT EXISTS ix_js_status_text ON training.js_status_documents((payload->>'status'));
CREATE OR REPLACE VIEW training.js_18 AS
SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='training' AND tablename='js_status_documents';""", "Expression index подходит для частого равенства по одному стабильному пути."),
19: ("""CREATE OR REPLACE VIEW training.js_19 AS
SELECT order_id,array_agg(payment_type ORDER BY payment_sequence) AS payment_types
FROM staging.order_payments GROUP BY order_id;""", "array_agg создаёт типизированный SQL-массив; порядок задан явно."),
20: ("""CREATE OR REPLACE VIEW training.js_20 AS
WITH src AS (SELECT order_id,array_agg(payment_type) payment_types FROM staging.order_payments GROUP BY order_id)
SELECT * FROM src WHERE 'credit_card'=ANY(payment_types);""", "ANY проверяет совпадение хотя бы с одним элементом массива."),
21: ("""CREATE OR REPLACE VIEW training.js_21 AS
WITH src AS (SELECT order_id,array_agg(payment_type ORDER BY payment_sequence) payment_types FROM staging.order_payments GROUP BY order_id)
SELECT s.order_id,u.payment_type FROM src s CROSS JOIN LATERAL unnest(s.payment_types) u(payment_type);""", "unnest разворачивает массив; grain становится элементом массива заказа."),
22: ("""CREATE OR REPLACE VIEW training.js_22 AS
SELECT product_id,array_agg(DISTINCT seller_id ORDER BY seller_id) AS seller_ids
FROM staging.order_items GROUP BY product_id;""", "array_agg собирает уникальный упорядоченный список продавцов товара."),
23: ("""CREATE OR REPLACE VIEW training.js_23 AS
WITH src AS (SELECT order_id,array_agg(DISTINCT payment_type) payment_types FROM staging.order_payments GROUP BY order_id)
SELECT order_id,ARRAY(SELECT DISTINCT x FROM unnest(payment_types) x ORDER BY x) AS unique_types FROM src;""", "Разворачивание, DISTINCT и повторная сборка удаляют дубли массива."),
24: ("""CREATE OR REPLACE VIEW training.js_24 AS
WITH a AS (SELECT ARRAY['credit_card','voucher','boleto']::text[] values_a),
b AS (SELECT ARRAY['voucher','debit_card']::text[] values_b)
SELECT ARRAY(SELECT unnest(values_a) INTERSECT SELECT unnest(values_b)) AS common_values FROM a,b;""", "Пересечение массивов выражено как пересечение двух множеств элементов."),
25: ("""CREATE OR REPLACE VIEW training.js_25 AS
SELECT ARRAY[[1,2,3],[4,5,6]]::int[] AS matrix,
       (ARRAY[[1,2,3],[4,5,6]]::int[])[2][1] AS row2_col1
FROM staging.orders LIMIT 1;""", "Многомерный массив прямоугольный; индексация PostgreSQL начинается с единицы."),
26: ("""CREATE OR REPLACE VIEW training.js_26 AS
WITH src AS (SELECT order_id,array_agg(payment_type ORDER BY payment_sequence) payment_types FROM staging.order_payments GROUP BY order_id)
SELECT s.order_id,u.position,u.payment_type FROM src s
CROSS JOIN LATERAL unnest(s.payment_types) WITH ORDINALITY u(payment_type,position);""", "WITH ORDINALITY сохраняет позицию элемента после разворачивания."),
27: ("""CREATE OR REPLACE VIEW training.js_27 AS
SELECT o.order_id,jsonb_build_object('event_type','order_created','event_version',1,
 'occurred_at',o.purchased_at,'data',jsonb_build_object('customer_id',o.customer_id,'status',o.order_status)) AS event
FROM staging.orders o;""", "Событие содержит тип, версию, время и вложенные бизнес-данные."),
28: ("""CREATE OR REPLACE VIEW training.js_28 AS
WITH events AS (SELECT order_id,jsonb_build_object('event_type','order_created','occurred_at',purchased_at,
 'data',jsonb_build_object('customer_id',customer_id)) payload FROM staging.orders)
SELECT order_id,payload,
 payload ?& ARRAY['event_type','occurred_at','data']
 AND jsonb_typeof(payload->'data')='object'
 AND nullif(payload->>'event_type','') IS NOT NULL AS is_valid
FROM events;""", "Проверяем обязательные ключи, непустое значение и тип вложенного объекта."),
29: ("""CREATE OR REPLACE VIEW training.js_29 AS
WITH events AS (SELECT order_id,jsonb_build_object('status',order_status,'customer_id',customer_id,
 'purchased_at',purchased_at) payload FROM staging.orders)
SELECT order_id,payload->>'customer_id' AS customer_id,payload->>'status' AS status,
       (payload->>'purchased_at')::timestamp AS purchased_at
FROM events;""", "JSON преобразован в типизированные реляционные колонки с явным cast."),
30: ("""CREATE OR REPLACE VIEW training.js_30 AS
WITH items AS (SELECT order_id,jsonb_agg(jsonb_build_object('item_id',order_item_id,'product_id',product_id,
 'price',price) ORDER BY order_item_id) items FROM staging.order_items GROUP BY order_id),
payments AS (SELECT order_id,array_agg(DISTINCT payment_type ORDER BY payment_type) payment_types,
 sum(payment_value) payment_total FROM staging.order_payments GROUP BY order_id)
SELECT o.order_id,o.customer_id,o.order_status,o.purchased_at,p.payment_total,p.payment_types,
       coalesce(i.items,'[]'::jsonb) AS items,
       jsonb_build_object('delivered_at',o.delivered_to_customer_at,'estimated_at',o.estimated_delivery_at) AS delivery
FROM staging.orders o LEFT JOIN items i USING(order_id) LEFT JOIN payments p USING(order_id);""", "Гибридная витрина сохраняет основные атрибуты колонками, повторяющиеся элементы — JSONB/массивами."),
}
