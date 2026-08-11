"""Эталонные решения модуля планов, индексов и оптимизации."""
SOLUTIONS={
1:("""CREATE OR REPLACE VIEW training.op_01 AS
SELECT order_id,order_status,purchased_at FROM training.op_orders WHERE order_status='delivered';
-- EXPLAIN SELECT * FROM training.op_01;""","Читаем план сверху вниз: VIEW раскрывается, а узел scan показывает способ доступа к физической таблице."),
2:("""CREATE OR REPLACE VIEW training.op_02 AS
SELECT date_trunc('month',purchased_at)::date AS month,count(*) AS orders_count
FROM training.op_orders GROUP BY 1;
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_02;""","ANALYZE действительно выполняет запрос; сравниваем estimated и actual rows на узлах scan и aggregate."),
3:("""CREATE OR REPLACE VIEW training.op_03 AS
SELECT * FROM training.op_orders WHERE order_status='delivered';
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_03;""","Частый статус возвращает большую долю таблицы, поэтому Seq Scan может быть дешевле множества обращений к индексу."),
4:("""CREATE INDEX IF NOT EXISTS ix_op_orders_order_id ON training.op_orders(order_id);
CREATE OR REPLACE VIEW training.op_04 AS
SELECT * FROM training.op_orders WHERE order_id='00010242fe8c5a6d1ba2dd792cb16214';
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_04;""","Высокоселективное равенство по order_id соответствует B-tree и обычно приводит к Index Scan."),
5:("""CREATE INDEX IF NOT EXISTS ix_op_orders_purchased_at ON training.op_orders(purchased_at);
CREATE OR REPLACE VIEW training.op_05 AS SELECT * FROM training.op_orders
WHERE purchased_at>=timestamp '2018-01-01' AND purchased_at<timestamp '2018-02-01';
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_05;""","Полуинтервал по исходной timestamp-колонке позволяет B-tree выполнить диапазонный поиск."),
6:("""CREATE INDEX IF NOT EXISTS ix_op_orders_status_date ON training.op_orders(order_status,purchased_at);
CREATE OR REPLACE VIEW training.op_06 AS SELECT * FROM training.op_orders
WHERE order_status='delivered' AND purchased_at>=timestamp '2018-01-01' AND purchased_at<timestamp '2018-02-01';
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_06;""","Равенство ведущей колонки и диапазон второй соответствуют порядку составного индекса."),
7:("""CREATE INDEX IF NOT EXISTS ix_op_orders_date_status ON training.op_orders(purchased_at,order_status);
CREATE OR REPLACE VIEW training.op_07 AS SELECT order_id,order_status,purchased_at FROM training.op_orders
WHERE purchased_at>=timestamp '2018-01-01' AND purchased_at<timestamp '2018-02-01' AND order_status='delivered';
-- Сравните план с op_06.""","При диапазоне на первой колонке использование следующей колонки для навигации ограничено; сравниваем два порядка на одном результате."),
8:("""CREATE INDEX IF NOT EXISTS ix_op_orders_status_cover ON training.op_orders(order_status) INCLUDE(order_id,purchased_at);
CREATE OR REPLACE VIEW training.op_08 AS SELECT order_id,purchased_at FROM training.op_orders WHERE order_status='canceled';
-- VACUUM (ANALYZE) training.op_orders;
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_08;""","INCLUDE хранит возвращаемые колонки в индексе и после VACUUM может дать Index Only Scan."),
9:("""CREATE INDEX IF NOT EXISTS ix_op_orders_canceled ON training.op_orders(purchased_at) WHERE order_status='canceled';
CREATE OR REPLACE VIEW training.op_09 AS SELECT order_id,purchased_at FROM training.op_orders
WHERE order_status='canceled' AND purchased_at>=timestamp '2018-01-01';
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_09;""","Partial index хранит только отменённые заказы и используется, когда предикат запроса логически включает условие индекса."),
10:("""CREATE INDEX IF NOT EXISTS ix_op_orders_status_lower ON training.op_orders(lower(order_status));
CREATE OR REPLACE VIEW training.op_10 AS SELECT order_id,order_status FROM training.op_orders
WHERE lower(order_status)='delivered';
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_10;""","Expression index должен содержать то же выражение, которое находится в WHERE."),
11:("""CREATE INDEX IF NOT EXISTS ix_op_orders_date_desc ON training.op_orders(purchased_at DESC,order_id);
CREATE OR REPLACE VIEW training.op_11 AS SELECT order_id,purchased_at FROM training.op_orders
ORDER BY purchased_at DESC,order_id LIMIT 20;
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_11;""","Индекс совпадает с ORDER BY, поэтому сервер может остановить чтение после первых 20 записей без полной сортировки."),
12:("""CREATE INDEX IF NOT EXISTS ix_op_orders_id_cover ON training.op_orders(order_id) INCLUDE(order_status,purchased_at);
CREATE OR REPLACE VIEW training.op_12 AS SELECT order_id,order_status,purchased_at FROM training.op_orders
WHERE order_id>='0000' AND order_id<'0010';
-- VACUUM (ANALYZE) training.op_orders;
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_12;""","Все нужные колонки находятся в индексе; visibility map после VACUUM позволяет избежать heap fetch."),
13:("""CREATE INDEX IF NOT EXISTS ix_op_orders_status_bitmap ON training.op_orders(order_status);
CREATE OR REPLACE VIEW training.op_13 AS SELECT * FROM training.op_orders
WHERE order_status IN('canceled','unavailable');
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_13;""","Для нескольких значений и среднего объёма PostgreSQL может объединить bitmap и затем читать подходящие heap pages."),
14:("""CREATE OR REPLACE VIEW training.op_14 AS SELECT * FROM training.op_orders
WHERE purchased_at>=timestamp '2018-01-01' AND purchased_at<timestamp '2018-02-01';
-- Сравните с WHERE date_trunc('month',purchased_at)=date '2018-01-01'.
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_14;""","Функция над индексированной колонкой скрывает исходный порядок B-tree; диапазон сохраняет sargable-предикат."),
15:("""CREATE OR REPLACE VIEW training.op_15 AS SELECT * FROM training.op_orders
WHERE order_id='00010242fe8c5a6d1ba2dd792cb16214'::text;
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_15;""","Явно сравниваем одинаковые типы; преобразование индексированной колонки могло бы исключить обычный Index Cond."),
16:("""CREATE INDEX IF NOT EXISTS ix_op_orders_id_pattern ON training.op_orders(order_id text_pattern_ops);
CREATE OR REPLACE VIEW training.op_16 AS SELECT order_id FROM training.op_orders WHERE order_id LIKE '0001%';
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_16;""","Для prefix LIKE operator class text_pattern_ops даёт B-tree диапазон независимо от локали."),
17:("""ANALYZE training.op_orders;
CREATE OR REPLACE VIEW training.op_17 AS SELECT attname AS column_name,n_distinct,
most_common_vals::text AS most_common_vals,most_common_freqs::text AS most_common_freqs
FROM pg_stats WHERE schemaname='training' AND tablename='op_orders';""","ANALYZE собирает распределение, cardinality и частые значения; pg_stats показывает данные cost model."),
18:("""CREATE OR REPLACE VIEW training.op_18 AS SELECT order_status,count(*)actual_rows
FROM training.op_orders GROUP BY order_status;
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_orders WHERE order_status='canceled';""","Фактические counts помогают интерпретировать расхождение estimated/actual rows в плане фильтра."),
19:("""CREATE STATISTICS IF NOT EXISTS st_op_status_date (dependencies,mcv)
ON order_status,purchased_at FROM training.op_orders;
ANALYZE training.op_orders;
CREATE OR REPLACE VIEW training.op_19 AS SELECT statistics_name,attnames,kinds
FROM pg_stats_ext WHERE schemaname='training' AND statistics_name='st_op_status_date';""","Extended statistics описывает зависимость колонок, которую независимые одномерные оценки не видят."),
20:("""CREATE OR REPLACE VIEW training.op_20 AS SELECT o.order_id,o.order_status,c.customer_unique_id
FROM training.op_orders o JOIN staging.customers c ON c.customer_id=o.customer_id;
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_20;""","Hash Join строит hash по меньшей стороне и хорошо подходит для большого equi-join без требуемого порядка."),
21:("""CREATE INDEX IF NOT EXISTS ix_op_orders_customer_id ON training.op_orders(customer_id);
CREATE OR REPLACE VIEW training.op_21 AS SELECT o.order_id,c.customer_unique_id
FROM training.op_orders o JOIN staging.customers c ON c.customer_id=o.customer_id;
-- SET LOCAL enable_hashjoin=off; SET LOCAL enable_nestloop=off;
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_21;""","Merge Join требует упорядоченных входов; индексы или Sort могут предоставить порядок по ключу."),
22:("""CREATE OR REPLACE VIEW training.op_22 AS SELECT o.order_id,o.purchased_at,c.customer_unique_id
FROM training.op_orders o JOIN staging.customers c ON c.customer_id=o.customer_id
WHERE o.order_id='00010242fe8c5a6d1ba2dd792cb16214';
-- EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_22;""","Очень маленькая внешняя сторона и индексный поиск внутренней делают Nested Loop естественным выбором."),
23:("""CREATE OR REPLACE VIEW training.op_23 AS SELECT order_id,purchased_at,order_status
FROM training.op_orders ORDER BY purchased_at,order_id;
-- BEGIN; SET LOCAL work_mem='1MB'; EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM training.op_23; ROLLBACK;""","Sort Method и Disk в EXPLAIN показывают spill; work_mem меняем локально и сравниваем одинаковый запрос."),
24:("""CREATE OR REPLACE VIEW training.op_24 AS WITH monthly AS MATERIALIZED(
SELECT date_trunc('month',purchased_at)::date AS month,count(*) AS orders_count FROM training.op_orders GROUP BY 1)
SELECT * FROM monthly WHERE orders_count>100;
-- Сравните AS MATERIALIZED и AS NOT MATERIALIZED через EXPLAIN.""","MATERIALIZED фиксирует вычисление CTE и может мешать проталкиванию фильтра; сравнение нужно делать на одном результате."),
25:("""CREATE OR REPLACE VIEW training.op_25 AS SELECT o.order_id,o.customer_id,
(SELECT count(*) FROM training.op_orders x WHERE x.customer_id=o.customer_id)customer_orders
FROM training.op_orders o;""","Коррелированный подзапрос логически выполняется для текущего клиента; план покажет, удалось ли декоррелировать или используется SubPlan."),
26:("""CREATE OR REPLACE VIEW training.op_26 AS SELECT o.order_id,o.customer_id
FROM training.op_orders o WHERE EXISTS(
SELECT 1 FROM staging.order_payments p WHERE p.order_id=o.order_id AND p.payment_value>1000);""","EXISTS выражает полусоединение: нужны только заказы с совпадением, а строки платежей не размножают результат."),
27:("""CREATE TABLE IF NOT EXISTS training.op_orders_part(
order_id text,customer_id text,order_status text,purchased_at timestamp)PARTITION BY RANGE(purchased_at);
CREATE TABLE IF NOT EXISTS training.op_orders_part_2017 PARTITION OF training.op_orders_part
FOR VALUES FROM('2017-01-01')TO('2018-01-01');
CREATE TABLE IF NOT EXISTS training.op_orders_part_2018 PARTITION OF training.op_orders_part
FOR VALUES FROM('2018-01-01')TO('2019-01-01');
CREATE TABLE IF NOT EXISTS training.op_orders_part_default PARTITION OF training.op_orders_part DEFAULT;
INSERT INTO training.op_orders_part SELECT order_id,customer_id,order_status,purchased_at FROM training.op_orders
WHERE NOT EXISTS(SELECT 1 FROM training.op_orders_part LIMIT 1);
CREATE OR REPLACE VIEW training.op_27 AS SELECT * FROM training.op_orders_part
WHERE purchased_at>=timestamp '2018-01-01' AND purchased_at<timestamp '2018-02-01';
-- EXPLAIN SELECT * FROM training.op_27;""","Предикат совпадает с ключом partitioning, поэтому план должен исключить партиции вне января 2018."),
28:("""CREATE INDEX IF NOT EXISTS ix_op_orders_approved_at ON training.op_orders(approved_at);
CREATE OR REPLACE VIEW training.op_28 AS SELECT locktype,mode,granted
FROM pg_locks WHERE relation='training.op_orders'::regclass;
-- В двух сессиях наблюдайте блокировки обычного CREATE INDEX.""","Обычный CREATE INDEX конфликтует с записью сильнее concurrent-варианта; pg_locks показывает фактические режимы."),
29:("""-- Эту команду запускайте отдельной autocommit-ячейкой:
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_op_orders_delivered_at_concurrent
-- ON training.op_orders(delivered_to_customer_at);
CREATE INDEX IF NOT EXISTS ix_op_orders_delivered_at ON training.op_orders(delivered_to_customer_at);
CREATE OR REPLACE VIEW training.op_29 AS SELECT indexname,indexdef FROM pg_indexes
WHERE schemaname='training' AND tablename='op_orders' AND indexname LIKE '%delivered_at%';""","CONCURRENTLY нельзя выполнять внутри транзакционного блока; состояние построенного индекса проверяем через каталог."),
30:("""CREATE OR REPLACE VIEW training.op_30 AS SELECT order_status,count(*)rows_count,
min(purchased_at)first_at,max(purchased_at)last_at FROM training.op_orders GROUP BY order_status;
-- Сохраните EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) до изменения и после,
-- затем сравните execution time, actual rows, buffers и наличие Sort/Scan.""","Регрессия сравнивает одинаковый результат и несколько физических метрик, а не только одно случайное время."),
}
