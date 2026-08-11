"""Эталонные решения модуля JOIN и гранулярности."""
SOLUTIONS={
1:("""CREATE OR REPLACE VIEW training.jn_01 AS
SELECT o.order_id,o.purchased_at,c.customer_unique_id,c.city,c.state
FROM staging.orders o JOIN staging.customers c ON c.customer_id=o.customer_id;""","Одна строка остаётся заказом: customer_id уникален в справочнике клиентов."),
2:("""CREATE OR REPLACE VIEW training.jn_02 AS
SELECT o.order_id,o.purchased_at,p.payment_sequence,p.payment_type,p.payment_value
FROM staging.orders o LEFT JOIN staging.order_payments p ON p.order_id=o.order_id;""","LEFT JOIN сохраняет заказ без платежа; grain результата — часть платежа заказа."),
3:("""CREATE OR REPLACE VIEW training.jn_03 AS
SELECT o.order_id FROM staging.orders o
WHERE NOT EXISTS(SELECT 1 FROM staging.order_payments p WHERE p.order_id=o.order_id);""","NOT EXISTS выражает антисоединение и не зависит от NULL в правом наборе."),
4:("""CREATE OR REPLACE VIEW training.jn_04 AS
SELECT c.customer_id,c.customer_unique_id FROM staging.customers c
WHERE EXISTS(SELECT 1 FROM staging.orders o WHERE o.customer_id=c.customer_id);""","EXISTS возвращает клиента один раз независимо от количества его заказов."),
5:("""CREATE OR REPLACE VIEW training.jn_05 AS
SELECT i.order_id,i.order_item_id,i.product_id,p.category_name_english,i.price
FROM staging.order_items i JOIN staging.products p ON p.product_id=i.product_id;""","Ключ позиции `(order_id, order_item_id)` сохраняется после соединения N:1 с товаром."),
6:("""CREATE OR REPLACE VIEW training.jn_06 AS
SELECT i.order_id,i.order_item_id,o.purchased_at,c.customer_unique_id,i.product_id,i.price
FROM staging.order_items i JOIN staging.orders o ON o.order_id=i.order_id
JOIN staging.customers c ON c.customer_id=o.customer_id;""","Начинаем с таблицы позиций и присоединяем стороны 1, поэтому строка остаётся позицией заказа."),
7:("""CREATE OR REPLACE VIEW training.jn_07 AS WITH p AS(
SELECT order_id,sum(payment_value)payment_total,count(*)payments_count FROM staging.order_payments GROUP BY order_id)
SELECT o.order_id,o.purchased_at,p.payment_total,p.payments_count FROM staging.orders o LEFT JOIN p USING(order_id);""","Платежи сначала агрегируются до grain заказа, поэтому JOIN не размножает заказы."),
8:("""CREATE OR REPLACE VIEW training.jn_08 AS WITH i AS(
SELECT order_id,count(*)items_count,sum(price)product_total,sum(freight_value)freight_total FROM staging.order_items GROUP BY order_id)
SELECT o.order_id,o.purchased_at,i.items_count,i.product_total,i.freight_total FROM staging.orders o LEFT JOIN i USING(order_id);""","Позиции сворачиваются до одной строки заказа перед соединением."),
9:("""CREATE OR REPLACE VIEW training.jn_09 AS SELECT o.order_id,
count(*)joined_rows,count(p.payment_value)payment_rows FROM staging.orders o
LEFT JOIN staging.order_payments p ON p.order_id=o.order_id GROUP BY o.order_id;""","COUNT(*) считает сохранённую строку LEFT JOIN, а COUNT(payment_value) игнорирует NULL отсутствующего платежа."),
10:("""CREATE OR REPLACE VIEW training.jn_10 AS SELECT o.order_id,
(p.order_id IS NULL)payment_missing,p.payment_value FROM staging.orders o
LEFT JOIN staging.order_payments p ON p.order_id=o.order_id WHERE p.order_id IS NULL;""","Признак отсутствия проверяем по ключу правой стороны; фильтр оставляет только unmatched-заказы."),
11:("""CREATE OR REPLACE VIEW training.jn_11 AS
SELECT zip_code_prefix,count(*)rows_count,count(DISTINCT (latitude,longitude))coordinate_variants
FROM staging.geolocation GROUP BY zip_code_prefix HAVING count(*)>1;""","До JOIN со справочником измеряем повторяемость ключа и число вариантов координат."),
12:("""CREATE OR REPLACE VIEW training.jn_12 AS WITH i AS(
SELECT order_id,count(*)item_rows FROM staging.order_items GROUP BY order_id),p AS(
SELECT order_id,count(*)payment_rows FROM staging.order_payments GROUP BY order_id)
SELECT i.order_id,item_rows,payment_rows,item_rows*payment_rows potential_join_rows
FROM i JOIN p USING(order_id) WHERE item_rows>1 AND payment_rows>1;""","Произведение кратностей показывает ожидаемое размножение прямого many-to-many JOIN."),
13:("""CREATE OR REPLACE VIEW training.jn_13 AS WITH months AS(
SELECT generate_series(date '2016-01-01',date '2018-12-01',interval '1 month')::date month_start)
SELECT m.month_start,count(o.order_id)orders_count FROM months m LEFT JOIN staging.orders o
ON o.purchased_at>=m.month_start AND o.purchased_at<m.month_start+interval '1 month' GROUP BY m.month_start;""","Заказ попадает в месячный полуинтервал `[start,next_start)`, а календарь сохраняет пустые месяцы."),
14:("""CREATE OR REPLACE VIEW training.jn_14 AS SELECT a.month earlier_month,b.month later_month,
a.revenue earlier_revenue,b.revenue later_revenue FROM mart.monthly_sales a
JOIN mart.monthly_sales b ON a.month<b.month;""","Неравенство создаёт все упорядоченные пары месяцев; grain — пара earlier/later."),
15:("""CREATE OR REPLACE VIEW training.jn_15 AS SELECT a.customer_id customer_a,b.customer_id customer_b,a.state
FROM staging.customers a JOIN staging.customers b ON b.state=a.state AND b.customer_id>a.customer_id;""","Условие `b.id > a.id` исключает совпадение с собой и зеркальные пары."),
16:("""CREATE OR REPLACE VIEW training.jn_16 AS SELECT c.customer_unique_id,last_order.order_id,last_order.purchased_at
FROM mart.customer_summary c CROSS JOIN LATERAL(
SELECT f.order_id,f.purchased_at FROM mart.order_finance f WHERE f.customer_unique_id=c.customer_unique_id
ORDER BY f.purchased_at DESC,f.order_id DESC LIMIT 1)last_order;""","LATERAL выполняет top-1 для текущего покупателя; grain остаётся одним покупателем."),
17:("""CREATE OR REPLACE VIEW training.jn_17 AS WITH states AS(SELECT DISTINCT state FROM staging.customers)
SELECT s.state,x.order_id,x.payment_value FROM states s CROSS JOIN LATERAL(
SELECT f.order_id,f.payment_value FROM mart.order_finance f JOIN staging.customers c ON c.customer_id=f.customer_id
WHERE c.state=s.state ORDER BY f.payment_value DESC,f.order_id LIMIT 3)x;""","LATERAL возвращает не более трёх заказов для каждой строки-штата."),
18:("""CREATE OR REPLACE VIEW training.jn_18 AS WITH i AS(
SELECT order_id,sum(price+freight_value)item_total FROM staging.order_items GROUP BY order_id),p AS(
SELECT order_id,sum(payment_value)payment_total FROM staging.order_payments GROUP BY order_id)
SELECT coalesce(i.order_id,p.order_id)order_id,i.item_total,p.payment_total,
CASE WHEN i.order_id IS NULL THEN 'payment_only' WHEN p.order_id IS NULL THEN 'item_only' ELSE 'both' END match_type
FROM i FULL JOIN p USING(order_id);""","Обе стороны предварительно имеют grain заказа; FULL JOIN сохраняет несовпавшие ключи для сверки."),
19:("""CREATE OR REPLACE VIEW training.jn_19 AS
SELECT state FROM staging.customers UNION SELECT state FROM staging.sellers;""","UNION объединяет штаты двух источников и удаляет дубли; UNION ALL использовался бы для сохранения повторов."),
20:("""CREATE OR REPLACE VIEW training.jn_20 AS
SELECT 'both' set_name,state FROM(SELECT state FROM staging.customers INTERSECT SELECT state FROM staging.sellers)x
UNION ALL SELECT 'customer_only',state FROM(SELECT state FROM staging.customers EXCEPT SELECT state FROM staging.sellers)y
UNION ALL SELECT 'seller_only',state FROM(SELECT state FROM staging.sellers EXCEPT SELECT state FROM staging.customers)z;""","INTERSECT находит общие значения, два EXCEPT — значения только одной стороны; метка сохраняет происхождение."),
21:("""CREATE OR REPLACE VIEW training.jn_21 AS
SELECT c.state,p.category_name_english,sum(i.price)revenue,count(*)item_rows,
grouping(c.state)state_total,grouping(p.category_name_english)category_total
FROM staging.order_items i JOIN staging.orders o USING(order_id)
JOIN staging.customers c USING(customer_id) JOIN staging.products p USING(product_id)
GROUP BY GROUPING SETS((c.state,p.category_name_english),(c.state),(p.category_name_english),());""","После JOIN на grain позиции GROUPING SETS строит детализацию и итоги одним проходом; GROUPING отличает итоговый NULL."),
22:("""CREATE OR REPLACE VIEW training.jn_22 AS
SELECT o.order_id,o.purchased_at,coalesce(sum(p.payment_value),0)payment_total,count(p.payment_sequence)payment_parts
FROM staging.orders o LEFT JOIN staging.order_payments p USING(order_id) GROUP BY o.order_id,o.purchased_at;""","Группировка возвращает платежи на уровень заказа и сохраняет заказы без платежей."),
23:("""CREATE OR REPLACE VIEW training.jn_23 AS
SELECT category_name_english,count(*)products_count,sum(orders_count)orders_count,sum(revenue)revenue
FROM mart.product_sales GROUP BY category_name_english;""","Агрегируем готовый grain товара до одной строки категории."),
24:("""CREATE OR REPLACE VIEW training.jn_24 AS
SELECT s.state,s.seller_id,count(DISTINCT i.order_id)orders_count,sum(i.price)revenue
FROM staging.order_items i JOIN staging.sellers s USING(seller_id) GROUP BY s.state,s.seller_id;""","Строка результата — продавец в штате; DISTINCT order_id защищает число заказов от нескольких позиций."),
25:("""CREATE OR REPLACE VIEW training.jn_25 AS
SELECT customer_unique_id,count(*)orders_count,
avg(delivered_to_customer_at::date-purchased_at::date)avg_delivery_days,
count(*)FILTER(WHERE delivered_late)late_orders
FROM mart.order_finance GROUP BY customer_unique_id;""","Витрина уже имеет grain заказа, поэтому показатели доставки безопасно агрегируются на клиента."),
26:("""CREATE OR REPLACE VIEW training.jn_26 AS WITH state_orders AS(
SELECT c.state,f.order_id,f.payment_value FROM mart.order_finance f JOIN staging.customers c USING(customer_id))
SELECT state,sum(payment_value)total_payment,count(*)orders_count,
sum(payment_value)/nullif(count(*),0)correct_average_order_value FROM state_orders GROUP BY state;""","Правильное общее среднее считается как сумма исходных значений, делённая на их количество, а не AVG средних групп."),
27:("""CREATE OR REPLACE VIEW training.jn_27 AS
SELECT category_name_english,sum(revenue)revenue,sum(orders_count)orders_count,
sum(revenue)/nullif(sum(orders_count),0)weighted_average_order_value
FROM mart.product_sales GROUP BY category_name_english;""","Вес товара — число заказов; отношение общих сумм эквивалентно корректному взвешенному среднему."),
28:("""CREATE OR REPLACE VIEW training.jn_28 AS WITH p AS(
SELECT order_id,sum(payment_value)payment_total FROM staging.order_payments GROUP BY order_id),j AS(
SELECT o.order_id,p.payment_total FROM staging.orders o LEFT JOIN p USING(order_id))
SELECT (SELECT sum(payment_value)FROM staging.order_payments)source_payment_total,
(SELECT sum(payment_total)FROM j)joined_payment_total,
(SELECT sum(payment_value)FROM staging.order_payments) IS NOT DISTINCT FROM (SELECT sum(payment_total)FROM j)totals_match;""","Сверяем аддитивную метрику до и после безопасного JOIN на одинаковом уровне заказа."),
29:("""CREATE OR REPLACE VIEW training.jn_29 AS WITH mart AS(
SELECT o.order_id,c.customer_unique_id,o.purchased_at FROM staging.orders o JOIN staging.customers c USING(customer_id))
SELECT count(*)rows_count,count(DISTINCT order_id)unique_orders,
count(*)=count(DISTINCT order_id)grain_is_unique FROM mart;""","Отдельная контрольная строка доказывает, что кандидатный ключ order_id уникален в результате."),
30:("""CREATE OR REPLACE VIEW training.jn_30 AS WITH items AS(
SELECT order_id,count(*)items_count,sum(price)product_value,sum(freight_value)freight_value FROM staging.order_items GROUP BY order_id),
payments AS(SELECT order_id,sum(payment_value)payment_value FROM staging.order_payments GROUP BY order_id)
SELECT o.order_id,o.order_status,o.purchased_at,c.customer_unique_id,c.state,
coalesce(i.items_count,0)items_count,i.product_value,i.freight_value,p.payment_value
FROM staging.orders o JOIN staging.customers c USING(customer_id)
LEFT JOIN items i USING(order_id) LEFT JOIN payments p USING(order_id);""","Каждая detail-таблица сначала свёрнута до order_id, поэтому итоговая витрина гарантирует одну строку заказа."),
}
