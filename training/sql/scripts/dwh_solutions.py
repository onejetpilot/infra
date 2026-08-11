"""Эталонные решения модуля моделирования DWH."""
SOLUTIONS={
1:("""CREATE OR REPLACE VIEW training.dw_01 AS
SELECT order_id,order_item_id,product_id,seller_id,price,freight_value
FROM staging.order_items;""","Grain формулируется до DDL: одна строка — одна позиция `(order_id, order_item_id)`."),
2:("""CREATE TABLE IF NOT EXISTS training.dw_dim_customer(
customer_sk bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,customer_unique_id text UNIQUE NOT NULL,city text,state text);
INSERT INTO training.dw_dim_customer(customer_unique_id,city,state)
SELECT DISTINCT ON(customer_unique_id)customer_unique_id,city,state FROM staging.customers ORDER BY customer_unique_id,customer_id
ON CONFLICT(customer_unique_id)DO NOTHING;
CREATE OR REPLACE VIEW training.dw_02 AS SELECT customer_sk,customer_unique_id FROM training.dw_dim_customer;""","Business key связывает источник, surrogate key изолирует факты от формата и будущей истории бизнес-ключа."),
3:("""INSERT INTO training.dw_dim_customer(customer_unique_id,city,state)
SELECT DISTINCT ON(customer_unique_id)customer_unique_id,city,state FROM staging.customers ORDER BY customer_unique_id,customer_id
ON CONFLICT(customer_unique_id)DO UPDATE SET city=excluded.city,state=excluded.state;
CREATE OR REPLACE VIEW training.dw_03 AS SELECT * FROM training.dw_dim_customer;""","Измерение клиента содержит одну строку business key и описательные атрибуты."),
4:("""CREATE TABLE IF NOT EXISTS training.dw_dim_product(
product_sk bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,product_id text UNIQUE NOT NULL,category_name text,weight_g numeric);
INSERT INTO training.dw_dim_product(product_id,category_name,weight_g)
SELECT product_id,category_name_english,weight_g FROM staging.products
ON CONFLICT(product_id)DO UPDATE SET category_name=excluded.category_name,weight_g=excluded.weight_g;
CREATE OR REPLACE VIEW training.dw_04 AS SELECT * FROM training.dw_dim_product;""","Product business key получает независимый surrogate key и аналитические атрибуты."),
5:("""CREATE TABLE IF NOT EXISTS training.dw_dim_seller(
seller_sk bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,seller_id text UNIQUE NOT NULL,city text,state text);
INSERT INTO training.dw_dim_seller(seller_id,city,state)SELECT seller_id,city,state FROM staging.sellers
ON CONFLICT(seller_id)DO UPDATE SET city=excluded.city,state=excluded.state;
CREATE OR REPLACE VIEW training.dw_05 AS SELECT * FROM training.dw_dim_seller;""","Измерение продавца отделяет описательные признаки от факта продажи."),
6:("""CREATE TABLE IF NOT EXISTS training.dw_dim_date(
date_sk integer PRIMARY KEY,calendar_date date UNIQUE NOT NULL,year_num int,quarter_num int,month_num int,day_num int,is_weekend boolean);
INSERT INTO training.dw_dim_date
SELECT to_char(d,'YYYYMMDD')::int,d,extract(year FROM d)::int,extract(quarter FROM d)::int,
extract(month FROM d)::int,extract(day FROM d)::int,extract(isodow FROM d)IN(6,7)
FROM generate_series(date '2016-01-01',date '2019-12-31',interval '1 day')d ON CONFLICT DO NOTHING;
CREATE OR REPLACE VIEW training.dw_06 AS SELECT * FROM training.dw_dim_date;""","Календарное измерение содержит непрерывные даты и готовые атрибуты группировки."),
7:("""CREATE TABLE IF NOT EXISTS training.dw_fact_order_item(
order_id text NOT NULL,order_item_id int NOT NULL,date_sk int,customer_sk bigint,product_sk bigint,seller_sk bigint,
price numeric,freight_value numeric,PRIMARY KEY(order_id,order_item_id));
INSERT INTO training.dw_fact_order_item
SELECT i.order_id,i.order_item_id,d.date_sk,dc.customer_sk,dp.product_sk,ds.seller_sk,i.price,i.freight_value
FROM staging.order_items i JOIN staging.orders o USING(order_id)JOIN staging.customers c USING(customer_id)
JOIN training.dw_dim_customer dc USING(customer_unique_id)JOIN training.dw_dim_product dp USING(product_id)
JOIN training.dw_dim_seller ds USING(seller_id)JOIN training.dw_dim_date d ON d.calendar_date=o.purchased_at::date
ON CONFLICT(order_id,order_item_id)DO UPDATE SET price=excluded.price,freight_value=excluded.freight_value;
CREATE OR REPLACE VIEW training.dw_07 AS SELECT * FROM training.dw_fact_order_item;""","Факт сохраняет grain позиции, degenerate order_id, foreign surrogate keys и аддитивные суммы."),
8:("""CREATE TABLE IF NOT EXISTS training.dw_fact_payment(
order_id text NOT NULL,payment_sequence int NOT NULL,customer_sk bigint,payment_type text,installments int,payment_value numeric,
PRIMARY KEY(order_id,payment_sequence));
INSERT INTO training.dw_fact_payment SELECT p.order_id,p.payment_sequence,d.customer_sk,p.payment_type,p.installments,p.payment_value
FROM staging.order_payments p JOIN staging.orders o USING(order_id)JOIN staging.customers c USING(customer_id)
JOIN training.dw_dim_customer d USING(customer_unique_id)
ON CONFLICT(order_id,payment_sequence)DO UPDATE SET payment_value=excluded.payment_value;
CREATE OR REPLACE VIEW training.dw_08 AS SELECT * FROM training.dw_fact_payment;""","Платёж имеет собственный grain `(order_id,payment_sequence)` и не смешивается с позициями заказа."),
9:("""CREATE TABLE IF NOT EXISTS training.dw_accum_delivery(
order_id text PRIMARY KEY,purchased_at timestamp,approved_at timestamp,delivered_at timestamp,estimated_at timestamp,order_status text);
INSERT INTO training.dw_accum_delivery SELECT order_id,purchased_at,approved_at,delivered_to_customer_at,estimated_delivery_at,order_status
FROM staging.orders ON CONFLICT(order_id)DO UPDATE SET approved_at=excluded.approved_at,delivered_at=excluded.delivered_at,
estimated_at=excluded.estimated_at,order_status=excluded.order_status;
CREATE OR REPLACE VIEW training.dw_09 AS SELECT * FROM training.dw_accum_delivery;""","Accumulating snapshot обновляет одну строку заказа по мере наступления этапов жизненного цикла."),
10:("""CREATE TABLE IF NOT EXISTS training.dw_periodic_sales(
snapshot_month date,state text,orders_count bigint,revenue numeric,PRIMARY KEY(snapshot_month,state));
INSERT INTO training.dw_periodic_sales
SELECT date_trunc('month',f.purchased_at)::date,c.state,count(*),sum(f.payment_value)
FROM mart.order_finance f JOIN staging.customers c USING(customer_id)GROUP BY 1,2
ON CONFLICT(snapshot_month,state)DO UPDATE SET orders_count=excluded.orders_count,revenue=excluded.revenue;
CREATE OR REPLACE VIEW training.dw_10 AS SELECT * FROM training.dw_periodic_sales;""","Periodic snapshot фиксирует метрики за месяц и штат; период является частью grain."),
11:("""CREATE OR REPLACE VIEW training.dw_11 AS
SELECT order_id,order_item_id,date_sk,customer_sk,product_sk,seller_sk,price,freight_value
FROM training.dw_fact_order_item;""","order_id хранится прямо в факте как degenerate dimension: отдельной таблицы описаний для него не требуется."),
12:("""CREATE TABLE IF NOT EXISTS training.dw_dim_order_flags(
flags_sk bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,order_status text,delivered_late boolean,UNIQUE(order_status,delivered_late));
INSERT INTO training.dw_dim_order_flags(order_status,delivered_late)
SELECT DISTINCT order_status,coalesce(delivered_late,false)FROM mart.order_finance ON CONFLICT DO NOTHING;
CREATE OR REPLACE VIEW training.dw_12 AS SELECT * FROM training.dw_dim_order_flags;""","Небольшие низкокардинальные признаки объединяются в junk dimension вместо множества отдельных измерений."),
13:("""CREATE OR REPLACE VIEW training.dw_13 AS SELECT f.order_id,
p.date_sk purchase_date_sk,d.date_sk delivery_date_sk,e.date_sk estimated_date_sk
FROM mart.order_finance f JOIN training.dw_dim_date p ON p.calendar_date=f.purchased_at::date
LEFT JOIN training.dw_dim_date d ON d.calendar_date=f.delivered_to_customer_at::date
LEFT JOIN training.dw_dim_date e ON e.calendar_date=f.estimated_delivery_at::date;""","Одна dim_date играет разные роли; смысл каждого FK задаётся именем колонки факта."),
14:("""CREATE OR REPLACE VIEW training.dw_14 AS WITH i AS(
SELECT customer_sk,count(DISTINCT order_id)orders_with_items FROM training.dw_fact_order_item GROUP BY customer_sk),p AS(
SELECT customer_sk,count(DISTINCT order_id)orders_with_payments FROM training.dw_fact_payment GROUP BY customer_sk)
SELECT c.customer_sk,coalesce(i.orders_with_items,0)orders_with_items,coalesce(p.orders_with_payments,0)orders_with_payments
FROM training.dw_dim_customer c LEFT JOIN i USING(customer_sk)LEFT JOIN p USING(customer_sk);""","Оба факта сначала агрегируются до conformed customer_sk, поэтому их прямой JOIN не создаёт N:M."),
15:("""INSERT INTO training.dw_dim_customer(customer_unique_id,city,state)
VALUES('__UNKNOWN__','Unknown','NA')ON CONFLICT(customer_unique_id)DO NOTHING;
CREATE OR REPLACE VIEW training.dw_15 AS SELECT * FROM training.dw_dim_customer WHERE customer_unique_id='__UNKNOWN__';""","Unknown member даёт обязательный surrogate key факту даже при отсутствующем бизнес-ключе измерения."),
16:("""INSERT INTO training.dw_dim_customer(customer_unique_id,city,state)
VALUES('__LATE_CUSTOMER__','Unknown','NA')ON CONFLICT(customer_unique_id)DO NOTHING;
UPDATE training.dw_dim_customer SET city='Resolved city',state='SP'
WHERE customer_unique_id='__LATE_CUSTOMER__';
CREATE OR REPLACE VIEW training.dw_16 AS SELECT * FROM training.dw_dim_customer WHERE customer_unique_id='__LATE_CUSTOMER__';""","Late-arriving member сначала получает inferred-запись с постоянным SK, затем атрибуты дополняются без изменения fact FK."),
17:("""UPDATE training.dw_dim_customer d SET city=s.city,state=s.state
FROM(SELECT DISTINCT ON(customer_unique_id)customer_unique_id,city,state FROM staging.customers ORDER BY customer_unique_id,customer_id)s
WHERE d.customer_unique_id=s.customer_unique_id AND(d.city,d.state)IS DISTINCT FROM(s.city,s.state);
CREATE OR REPLACE VIEW training.dw_17 AS SELECT * FROM training.dw_dim_customer;""","SCD1 перезаписывает текущие атрибуты на том же surrogate key и не сохраняет историю."),
18:("""CREATE TABLE IF NOT EXISTS training.dw_dim_customer_scd2(
customer_sk bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,customer_unique_id text NOT NULL,city text,state text,
valid_from timestamp NOT NULL,valid_to timestamp,is_current boolean NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS ux_dw_customer_scd2_current ON training.dw_dim_customer_scd2(customer_unique_id)WHERE is_current;
INSERT INTO training.dw_dim_customer_scd2(customer_unique_id,city,state,valid_from,is_current)
SELECT DISTINCT ON(customer_unique_id)customer_unique_id,city,state,timestamp '1900-01-01',true FROM staging.customers s
WHERE NOT EXISTS(SELECT 1 FROM training.dw_dim_customer_scd2 d WHERE d.customer_unique_id=s.customer_unique_id)
ORDER BY customer_unique_id,customer_id;
CREATE OR REPLACE VIEW training.dw_18 AS SELECT * FROM training.dw_dim_customer_scd2;""","SCD2 создаёт отдельный SK каждой версии и хранит историю полуинтервалами."),
19:("""CREATE OR REPLACE VIEW training.dw_19 AS SELECT *,
coalesce(valid_to,timestamp 'infinity')>valid_from valid_interval,
tstzrange(valid_from AT TIME ZONE 'UTC',coalesce(valid_to,timestamp 'infinity')AT TIME ZONE 'UTC','[)')valid_period
FROM training.dw_dim_customer_scd2;""","Полуинтервал `[valid_from,valid_to)` исключает двойное совпадение на границе версий."),
20:("""CREATE OR REPLACE VIEW training.dw_20 AS SELECT * FROM training.dw_dim_customer_scd2 WHERE is_current;
""","Текущая версия выбирается явным флагом; partial unique index гарантирует не более одной строки business key."),
21:("""CREATE OR REPLACE VIEW training.dw_21 AS SELECT i.order_id,i.order_item_id,d.customer_sk,d.city,d.state
FROM staging.order_items i JOIN staging.orders o USING(order_id)JOIN staging.customers c USING(customer_id)
JOIN training.dw_dim_customer_scd2 d ON d.customer_unique_id=c.customer_unique_id
AND o.purchased_at>=d.valid_from AND o.purchased_at<coalesce(d.valid_to,timestamp 'infinity');""","Point-in-time JOIN выбирает версию измерения, чей полуинтервал покрывает момент факта."),
22:("""CREATE OR REPLACE VIEW training.dw_22 AS SELECT date_sk,
sum(price)product_revenue,sum(freight_value)freight_revenue,count(*)item_rows
FROM training.dw_fact_order_item GROUP BY date_sk;""","Цена и доставка аддитивны по позициям и датам, поэтому их можно безопасно суммировать."),
23:("""CREATE TABLE IF NOT EXISTS training.dw_customer_ltv_snapshot(
snapshot_date date,customer_sk bigint,ltv_balance numeric,PRIMARY KEY(snapshot_date,customer_sk));
INSERT INTO training.dw_customer_ltv_snapshot
SELECT current_date,d.customer_sk,s.lifetime_value FROM mart.customer_summary s
JOIN training.dw_dim_customer d USING(customer_unique_id)ON CONFLICT DO NOTHING;
CREATE OR REPLACE VIEW training.dw_23 AS SELECT * FROM training.dw_customer_ltv_snapshot;""","Snapshot LTV суммируется по клиентам внутри одной даты, но не по разным snapshot_date: это полуаддитивная метрика по времени."),
24:("""CREATE OR REPLACE VIEW training.dw_24 AS SELECT date_sk,sum(price)revenue,count(*)item_count,
sum(price)/nullif(count(*),0)average_item_price FROM training.dw_fact_order_item GROUP BY date_sk;""","Среднее не складывается; его пересчитываем из аддитивных numerator и denominator на нужном уровне."),
25:("""CREATE OR REPLACE VIEW training.dw_25 AS SELECT f.order_id,f.order_item_id,d.calendar_date,
c.state,p.category_name,s.state seller_state,f.price,f.freight_value
FROM training.dw_fact_order_item f JOIN training.dw_dim_date d USING(date_sk)
JOIN training.dw_dim_customer c USING(customer_sk)JOIN training.dw_dim_product p USING(product_sk)
JOIN training.dw_dim_seller s USING(seller_sk);""","Star schema соединяет центральный факт непосредственно с денормализованными измерениями по surrogate keys."),
26:("""CREATE TABLE IF NOT EXISTS training.dw_dim_category(
category_sk bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,category_name text UNIQUE);
INSERT INTO training.dw_dim_category(category_name)SELECT DISTINCT category_name FROM training.dw_dim_product ON CONFLICT DO NOTHING;
CREATE OR REPLACE VIEW training.dw_26 AS SELECT p.product_sk,p.product_id,c.category_sk,c.category_name,p.weight_g
FROM training.dw_dim_product p LEFT JOIN training.dw_dim_category c USING(category_name);""","Snowflake выносит категорию из product dimension в отдельную нормализованную ветвь."),
27:("""CREATE TABLE IF NOT EXISTS training.dw_fact_customer_activity(
customer_sk bigint,date_sk int,activity_type text,PRIMARY KEY(customer_sk,date_sk,activity_type));
INSERT INTO training.dw_fact_customer_activity
SELECT DISTINCT c.customer_sk,d.date_sk,'purchase' FROM mart.order_finance f
JOIN training.dw_dim_customer c USING(customer_unique_id)JOIN training.dw_dim_date d ON d.calendar_date=f.purchased_at::date
ON CONFLICT DO NOTHING;
CREATE OR REPLACE VIEW training.dw_27 AS SELECT * FROM training.dw_fact_customer_activity;""","Factless fact фиксирует сам факт активности связкой измерений без числовой меры."),
28:("""CREATE TABLE IF NOT EXISTS training.dw_bridge_order_product(
order_id text,product_sk bigint,item_weight numeric,PRIMARY KEY(order_id,product_sk));
INSERT INTO training.dw_bridge_order_product
SELECT i.order_id,p.product_sk,count(*)::numeric/sum(count(*))OVER(PARTITION BY i.order_id)
FROM staging.order_items i JOIN training.dw_dim_product p USING(product_id)GROUP BY i.order_id,p.product_sk
ON CONFLICT(order_id,product_sk)DO UPDATE SET item_weight=excluded.item_weight;
CREATE OR REPLACE VIEW training.dw_28 AS SELECT * FROM training.dw_bridge_order_product;""","Bridge разрешает многозначную связь заказ–товар; веса внутри заказа дают единицу и предотвращают двойной учёт."),
29:("""CREATE OR REPLACE VIEW training.dw_29 AS SELECT d.calendar_date,c.state,p.category_name,
count(DISTINCT f.order_id)orders_count,sum(f.price)product_revenue,sum(f.freight_value)freight_revenue
FROM training.dw_fact_order_item f JOIN training.dw_dim_date d USING(date_sk)
JOIN training.dw_dim_customer c USING(customer_sk)JOIN training.dw_dim_product p USING(product_sk)
GROUP BY d.calendar_date,c.state,p.category_name;""","Витрина продаж имеет объявленный grain дата–штат–категория и аддитивные суммы из факта."),
30:("""CREATE OR REPLACE VIEW training.dw_30 AS SELECT
(SELECT count(*)FROM training.dw_fact_order_item)fact_rows,
(SELECT count(DISTINCT(order_id,order_item_id))FROM training.dw_fact_order_item)unique_grain,
(SELECT sum(price)FROM staging.order_items)source_revenue,
(SELECT sum(price)FROM training.dw_fact_order_item)fact_revenue,
(SELECT count(*)=count(DISTINCT(order_id,order_item_id))FROM training.dw_fact_order_item)grain_valid,
(SELECT sum(price)FROM staging.order_items)IS NOT DISTINCT FROM(SELECT sum(price)FROM training.dw_fact_order_item)reconciled;""","Финальная проверка одновременно доказывает уникальность grain и совпадение аддитивной выручки с источником."),
}
