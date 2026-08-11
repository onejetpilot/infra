"""Эталонные решения и короткие разборы для курса по функциям PostgreSQL."""

SOLUTIONS = {
    1: ("""CREATE OR REPLACE FUNCTION training.fn_01_full_name(first_name text, last_name text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT concat_ws(' ', nullif(trim(first_name), ''), nullif(trim(last_name), ''));
$$;""", "Очищаем обе части, превращаем пустые строки в NULL и соединяем оставшиеся части одним пробелом."),
    2: ("""CREATE OR REPLACE FUNCTION training.fn_02_add_tax(amount numeric, tax_percent numeric)
RETURNS numeric LANGUAGE sql IMMUTABLE AS $$
    SELECT round(amount * (1 + tax_percent / 100), 2);
$$;""", "Переводим процент в долю, прибавляем его к единице, умножаем сумму и округляем результат."),
    3: ("""CREATE OR REPLACE FUNCTION training.fn_03_safe_int(value text)
RETURNS integer LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    RETURN value::integer;
EXCEPTION WHEN invalid_text_representation OR numeric_value_out_of_range THEN
    RETURN NULL;
END;
$$;""", "Пробуем привести текст к integer. Ошибку неверного текста или переполнения перехватываем и возвращаем NULL."),
    4: ("""CREATE OR REPLACE FUNCTION training.fn_04_order_year(value timestamp)
RETURNS integer LANGUAGE sql IMMUTABLE AS $$
    SELECT extract(year FROM value)::integer;
$$;""", "EXTRACT достаёт год, после чего явно приводим результат к требуемому integer."),
    5: ("""CREATE OR REPLACE FUNCTION training.fn_05_delivery_days(p_order_id text)
RETURNS integer LANGUAGE sql STABLE AS $$
    SELECT delivered_to_customer_at::date - purchased_at::date
    FROM staging.orders WHERE order_id = p_order_id;
$$;""", "Находим заказ и вычитаем календарные даты. При неизвестном заказе или пустой доставке получится NULL."),
    6: ("""CREATE OR REPLACE FUNCTION training.fn_06_order_total(p_order_id text)
RETURNS numeric LANGUAGE sql STABLE AS $$
    SELECT round(sum(price + freight_value), 2)
    FROM staging.order_items WHERE order_id = p_order_id;
$$;""", "Оставляем позиции заказа, складываем цену и доставку каждой позиции, затем суммируем итог."),
    7: ("""CREATE OR REPLACE FUNCTION training.fn_07_customer_orders(p_customer_unique_id text)
RETURNS bigint LANGUAGE sql STABLE AS $$
    SELECT coalesce((SELECT orders_count FROM mart.customer_summary
                     WHERE customer_unique_id = p_customer_unique_id), 0)::bigint;
$$;""", "Берём готовое число заказов из витрины; COALESCE возвращает ноль для неизвестного покупателя."),
    8: ("""CREATE OR REPLACE FUNCTION training.fn_08_payment_label(amount numeric)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN amount < 100 THEN 'small'
                WHEN amount < 500 THEN 'medium'
                ELSE 'large' END;
$$;""", "CASE последовательно проверяет границы до 100 и до 500; остальные суммы относятся к large."),
    9: ("""CREATE OR REPLACE FUNCTION training.fn_09_is_late(p_order_id text)
RETURNS boolean LANGUAGE sql STABLE AS $$
    SELECT delivered_late FROM mart.order_finance WHERE order_id = p_order_id;
$$;""", "Не пересчитываем признак, а читаем готовое значение из витрины по ключу заказа."),
    10: ("""CREATE OR REPLACE FUNCTION training.fn_10_state_order_count(p_state text)
RETURNS bigint LANGUAGE sql STABLE AS $$
    SELECT count(*) FROM staging.orders o
    JOIN staging.customers c ON c.customer_id = o.customer_id
    WHERE c.state = p_state;
$$;""", "Соединяем заказ с покупателем, фильтруем штат и считаем строки заказов, а не клиентов."),
    11: ("""CREATE OR REPLACE FUNCTION training.fn_11_orders_between(date_from date, date_to date)
RETURNS TABLE(order_id text, purchased_at timestamp) LANGUAGE sql STABLE AS $$
    SELECT o.order_id, o.purchased_at FROM staging.orders o
    WHERE o.purchased_at >= date_from AND o.purchased_at < date_to;
$$;""", "Используем полуинтервал: начало включаем, конец не включаем. RETURNS TABLE задаёт форму каждой возвращаемой строки."),
    12: ("""CREATE OR REPLACE FUNCTION training.fn_12_top_customers(limit_rows integer DEFAULT 10)
RETURNS TABLE(customer_unique_id text, orders_count bigint, lifetime_value numeric)
LANGUAGE sql STABLE AS $$
    SELECT c.customer_unique_id, c.orders_count, c.lifetime_value
    FROM mart.customer_summary c
    ORDER BY c.lifetime_value DESC NULLS LAST, c.orders_count DESC, c.customer_unique_id
    LIMIT limit_rows;
$$;""", "Сортируем покупателей по LTV и числу заказов, добавляем стабильный tie-breaker и ограничиваем результат аргументом."),
    13: ("""CREATE OR REPLACE FUNCTION training.fn_13_category_revenue(p_category_name text)
RETURNS numeric LANGUAGE sql STABLE AS $$
    SELECT coalesce(round(sum(revenue), 2), 0)
    FROM mart.product_sales WHERE product_category_name = p_category_name;
$$;""", "Фильтруем категорию, суммируем её выручку и заменяем NULL на ноль для отсутствующей категории."),
    14: ("""CREATE OR REPLACE FUNCTION training.fn_14_order_status_summary()
RETURNS TABLE(order_status text, orders_count bigint) LANGUAGE sql STABLE AS $$
    SELECT o.order_status, count(*) FROM staging.orders o
    GROUP BY o.order_status ORDER BY o.order_status;
$$;""", "Группируем заказы по статусу. Одна строка результата соответствует одному статусу."),
    15: ("""CREATE OR REPLACE FUNCTION training.fn_15_customer_ltv(p_customer_unique_id text)
RETURNS numeric LANGUAGE sql STABLE AS $$
    SELECT coalesce((SELECT lifetime_value FROM mart.customer_summary
                     WHERE customer_unique_id = p_customer_unique_id), 0);
$$;""", "Читаем готовый LTV из витрины, а для неизвестного покупателя возвращаем ноль."),
    16: ("""CREATE OR REPLACE FUNCTION training.fn_16_product_dimensions(p_product_id text)
RETURNS jsonb LANGUAGE sql STABLE AS $$
    SELECT jsonb_build_object('product_id', product_id, 'weight_g', weight_g,
        'length_cm', length_cm, 'height_cm', height_cm, 'width_cm', width_cm)
    FROM staging.products WHERE product_id = p_product_id;
$$;""", "Находим товар и собираем JSON с точно заданными именами ключей."),
    17: ("""CREATE OR REPLACE FUNCTION training.fn_17_normalize_city(city text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT lower(regexp_replace(trim(city), '\\s+', ' ', 'g'));
$$;""", "Сначала убираем пробелы по краям, затем сжимаем внутренние пробелы и приводим текст к нижнему регистру."),
    18: ("""CREATE OR REPLACE FUNCTION training.fn_18_days_from_purchase(
    p_order_id text, as_of_date date DEFAULT current_date)
RETURNS integer LANGUAGE sql STABLE AS $$
    SELECT as_of_date - purchased_at::date
    FROM staging.orders WHERE order_id = p_order_id;
$$;""", "Берём дату покупки заказа и вычитаем её из переданной даты отсчёта; current_date работает как значение по умолчанию."),
    19: ("""CREATE OR REPLACE FUNCTION training.fn_19_percent_change(old_value numeric, new_value numeric)
RETURNS numeric LANGUAGE sql IMMUTABLE AS $$
    SELECT round(100 * (new_value - old_value) / nullif(old_value, 0), 2);
$$;""", "NULLIF превращает нулевое старое значение в NULL и предотвращает деление на ноль."),
    20: ("""CREATE OR REPLACE FUNCTION training.fn_20_existing_orders(order_ids text[])
RETURNS TABLE(order_id text) LANGUAGE sql STABLE AS $$
    SELECT o.order_id FROM staging.orders o
    WHERE o.order_id = ANY(order_ids) ORDER BY o.order_id;
$$;""", "ANY сравнивает ключ каждой строки со всеми элементами массива; несуществующие ключи просто не попадают в ответ."),
    21: ("""CREATE OR REPLACE FUNCTION training.fn_21_monthly_revenue(year_num integer)
RETURNS TABLE(month date, revenue numeric) LANGUAGE sql STABLE AS $$
    SELECT m.month, m.revenue FROM mart.monthly_sales m
    WHERE m.month >= make_date(year_num, 1, 1)
      AND m.month < make_date(year_num + 1, 1, 1)
    ORDER BY m.month;
$$;""", "Фильтруем год диапазоном дат, чтобы условие оставалось понятным и пригодным для индекса."),
    22: ("""CREATE OR REPLACE FUNCTION training.fn_22_seller_rank(p_seller_id text)
RETURNS bigint LANGUAGE sql STABLE AS $$
    SELECT seller_rank FROM (
        SELECT seller_id, dense_rank() OVER (ORDER BY sum(price) DESC)::bigint AS seller_rank
        FROM staging.order_items GROUP BY seller_id
    ) ranked WHERE seller_id = p_seller_id;
$$;""", "Сначала агрегируем выручку продавцов, затем ранжируем весь набор и только после этого выбираем нужного продавца."),
    23: ("""CREATE OR REPLACE FUNCTION training.fn_23_customer_profile(p_customer_unique_id text)
RETURNS jsonb LANGUAGE sql STABLE AS $$
    SELECT to_jsonb(x) FROM (
        SELECT customer_unique_id, orders_count, lifetime_value
        FROM mart.customer_summary WHERE customer_unique_id = p_customer_unique_id
    ) x;
$$;""", "Подзапрос задаёт точные поля профиля, а to_jsonb сохраняет их имена в JSON."),
    24: ("""CREATE OR REPLACE FUNCTION training.fn_24_search_orders(filters jsonb)
RETURNS TABLE(order_id text) LANGUAGE sql STABLE AS $$
    SELECT o.order_id FROM staging.orders o
    JOIN staging.customers c ON c.customer_id = o.customer_id
    WHERE (filters ->> 'status' IS NULL OR o.order_status = filters ->> 'status')
      AND (filters ->> 'state' IS NULL OR c.state = filters ->> 'state');
$$;""", "Каждый JSON-фильтр применяем только тогда, когда соответствующий ключ присутствует."),
    25: ("""CREATE OR REPLACE FUNCTION training.fn_25_table_row_count(schema_name text, table_name text)
RETURNS bigint LANGUAGE plpgsql STABLE AS $$
DECLARE result bigint;
BEGIN
    EXECUTE format('SELECT count(*) FROM %I.%I', schema_name, table_name) INTO result;
    RETURN result;
END;
$$;""", "Имена объектов нельзя передать параметрами запроса, поэтому безопасно экранируем их через format с %I."),
    26: ("""CREATE OR REPLACE FUNCTION training.fn_26_audit_event(event_name text, payload jsonb)
RETURNS bigint LANGUAGE plpgsql VOLATILE AS $$
DECLARE result bigint;
BEGIN
    INSERT INTO training.function_audit(event_name, payload)
    VALUES (event_name, payload) RETURNING audit_id INTO result;
    RETURN result;
END;
$$;""", "INSERT создаёт запись, RETURNING забирает её ключ. Из-за изменения таблицы функция явно объявлена VOLATILE."),
    27: ("""CREATE OR REPLACE FUNCTION training.fn_27_order_count()
RETURNS bigint LANGUAGE sql STABLE AS $$
    SELECT count(*) FROM staging.orders;
$$;""", "Функция читает таблицу, поэтому STABLE точнее, чем IMMUTABLE."),
    28: ("""CREATE OR REPLACE FUNCTION training.fn_28_distance_km(
    lat1 numeric, lon1 numeric, lat2 numeric, lon2 numeric)
RETURNS numeric LANGUAGE sql IMMUTABLE AS $$
    SELECT (6371 * 2 * asin(sqrt(
        power(sin(radians((lat2 - lat1)::double precision) / 2), 2) +
        cos(radians(lat1::double precision)) * cos(radians(lat2::double precision)) *
        power(sin(radians((lon2 - lon1)::double precision) / 2), 2)
    )))::numeric;
$$;""", "Переводим координаты в радианы и применяем формулу haversine с радиусом Земли 6371 км."),
    29: ("""CREATE OR REPLACE FUNCTION training.fn_29_cohort_retention(
    p_cohort_month date, p_month_offset integer)
RETURNS numeric LANGUAGE sql STABLE AS $$
WITH purchases AS (
    SELECT c.customer_unique_id, date_trunc('month', o.purchased_at)::date AS month
    FROM staging.orders o JOIN staging.customers c ON c.customer_id = o.customer_id
), cohorts AS (
    SELECT customer_unique_id, min(month) AS cohort_month FROM purchases GROUP BY customer_unique_id
), cohort_size AS (
    SELECT count(*)::numeric AS cnt FROM cohorts WHERE cohort_month = p_cohort_month
), retained AS (
    SELECT count(DISTINCT p.customer_unique_id)::numeric AS cnt
    FROM purchases p JOIN cohorts c USING (customer_unique_id)
    WHERE c.cohort_month = p_cohort_month
      AND p.month = (p_cohort_month + make_interval(months => p_month_offset))::date
)
SELECT round(100 * retained.cnt / nullif(cohort_size.cnt, 0), 2)
FROM retained CROSS JOIN cohort_size;
$$;""", "Определяем первый месяц каждого клиента, считаем размер когорты и долю клиентов, активных через заданное число месяцев."),
    30: ("""CREATE OR REPLACE FUNCTION training.fn_30_customer_segment(p_customer_unique_id text)
RETURNS text LANGUAGE plpgsql STABLE AS $$
DECLARE v_orders bigint; v_ltv numeric; v_max_ltv numeric;
BEGIN
    SELECT orders_count, lifetime_value INTO v_orders, v_ltv
    FROM mart.customer_summary WHERE customer_unique_id = p_customer_unique_id;
    IF NOT FOUND THEN RETURN 'unknown'; END IF;
    SELECT max(lifetime_value) INTO v_max_ltv FROM mart.customer_summary;
    IF v_ltv >= v_max_ltv THEN RETURN 'VIP';
    ELSIF v_orders > 1 THEN RETURN 'loyal';
    ELSE RETURN 'regular'; END IF;
END;
$$;""", "Сначала читаем профиль клиента и отдельно максимум LTV, затем проверяем ветви от самой приоритетной к обычной."),
}
