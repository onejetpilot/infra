"""Эталонные решения курса по процедурам PostgreSQL."""

SOLUTIONS = {
 1:("""CREATE OR REPLACE PROCEDURE training.pr_01_log_message(p_message text)
LANGUAGE plpgsql AS $$ BEGIN
  INSERT INTO training.procedure_log(message) VALUES (p_message);
END $$;""","Добавляем одну строку в журнал, передавая параметр в колонку message."),
 2:("""CREATE OR REPLACE PROCEDURE training.pr_02_log_event(p_event_name text, p_payload jsonb)
LANGUAGE plpgsql AS $$ BEGIN
  INSERT INTO training.procedure_log(event_name,payload) VALUES (p_event_name,p_payload);
END $$;""","Явно перечисляем две целевые колонки и записываем в них параметры процедуры."),
 3:("""CREATE OR REPLACE PROCEDURE training.pr_03_clear_log()
LANGUAGE plpgsql AS $$ BEGIN DELETE FROM training.procedure_log; END $$;""","DELETE без условия очищает только указанную учебную таблицу."),
 4:("""CREATE OR REPLACE PROCEDURE training.pr_04_add_customer(p_id text,p_city text,p_state text)
LANGUAGE plpgsql AS $$ BEGIN
  INSERT INTO training.customer_work(customer_unique_id,city,state) VALUES(p_id,p_city,p_state);
END $$;""","Создаём клиента, явно сопоставляя каждый параметр с колонкой."),
 5:("""CREATE OR REPLACE PROCEDURE training.pr_05_change_customer_city(p_id text,p_city text)
LANGUAGE plpgsql AS $$ BEGIN
  UPDATE training.customer_work SET city=p_city WHERE customer_unique_id=p_id;
END $$;""","UPDATE меняет только город выбранного ключом клиента."),
 6:("""CREATE OR REPLACE PROCEDURE training.pr_06_delete_customer(p_id text)
LANGUAGE plpgsql AS $$ BEGIN
  DELETE FROM training.customer_work WHERE customer_unique_id=p_id;
END $$;""","Точный WHERE ограничивает удаление одним покупателем."),
 7:("""CREATE OR REPLACE PROCEDURE training.pr_07_upsert_customer(p_id text,p_city text,p_state text)
LANGUAGE plpgsql AS $$ BEGIN
  INSERT INTO training.customer_work(customer_unique_id,city,state) VALUES(p_id,p_city,p_state)
  ON CONFLICT(customer_unique_id) DO UPDATE SET city=excluded.city,state=excluded.state;
END $$;""","INSERT создаёт клиента, а ON CONFLICT обновляет поля при повторном ключе."),
 8:("""CREATE OR REPLACE PROCEDURE training.pr_08_copy_customer(p_id text)
LANGUAGE plpgsql AS $$ BEGIN
  INSERT INTO training.customer_work(customer_unique_id,city,state)
  SELECT customer_unique_id,city,state FROM staging.customers WHERE customer_unique_id=p_id
  ON CONFLICT(customer_unique_id) DO NOTHING;
END $$;""","Копируем данные запросом INSERT SELECT и игнорируем уже существующий ключ."),
 9:("""CREATE OR REPLACE PROCEDURE training.pr_09_copy_state_customers(p_state text)
LANGUAGE plpgsql AS $$ BEGIN
  INSERT INTO training.customer_work(customer_unique_id,city,state)
  SELECT DISTINCT ON(c.customer_unique_id) c.customer_unique_id,c.city,c.state
  FROM staging.customers c WHERE c.state=p_state ORDER BY c.customer_unique_id,c.customer_id
  ON CONFLICT(customer_unique_id) DO NOTHING;
END $$;""","Фильтруем штат и оставляем одну строку на постоянный идентификатор клиента перед вставкой."),
 10:("""CREATE OR REPLACE PROCEDURE training.pr_10_count_state_customers(p_state text)
LANGUAGE plpgsql AS $$ DECLARE v_count bigint; BEGIN
  SELECT count(*) INTO v_count FROM staging.customers c WHERE c.state=p_state;
  INSERT INTO training.procedure_log(event_name,amount) VALUES('state_customer_count',v_count);
END $$;""","Сначала считаем клиентов в переменную, затем записываем число в числовое поле amount журнала."),
 11:("""CREATE OR REPLACE PROCEDURE training.pr_11_refresh_order_sample(p_limit integer)
LANGUAGE plpgsql AS $$ BEGIN
 DELETE FROM training.order_work;
 INSERT INTO training.order_work(order_id,customer_id,order_status,purchased_at)
 SELECT order_id,customer_id,order_status,purchased_at FROM staging.orders ORDER BY order_id LIMIT p_limit;
END $$;""","Очищаем рабочую копию и заново загружаем заданное количество заказов в стабильном порядке."),
 12:("""CREATE OR REPLACE PROCEDURE training.pr_12_load_orders_between(p_from date,p_to date)
LANGUAGE plpgsql AS $$ BEGIN
 INSERT INTO training.order_work(order_id,customer_id,order_status,purchased_at)
 SELECT order_id,customer_id,order_status,purchased_at FROM staging.orders
 WHERE purchased_at>=p_from AND purchased_at<p_to ON CONFLICT(order_id) DO NOTHING;
END $$;""","Фильтруем полуинтервал дат и защищаем повторный запуск от дублей."),
 13:("""CREATE OR REPLACE PROCEDURE training.pr_13_update_order_status(p_id text,p_status text)
LANGUAGE plpgsql AS $$ BEGIN
 UPDATE training.order_work SET order_status=p_status WHERE order_id=p_id;
END $$;""","Обновляем статус только строки с переданным ключом заказа."),
 14:("""CREATE OR REPLACE PROCEDURE training.pr_14_delete_cancelled_orders()
LANGUAGE plpgsql AS $$ BEGIN
 DELETE FROM training.order_work WHERE order_status IN ('canceled','unavailable');
END $$;""","Удаляем только два неактуальных статуса одним условием IN."),
 15:("""CREATE OR REPLACE PROCEDURE training.pr_15_mark_processed(p_id text)
LANGUAGE plpgsql AS $$ BEGIN
 UPDATE training.order_work SET processed_at=clock_timestamp() WHERE order_id=p_id;
END $$;""","Ставим реальное время обработки выбранному заказу."),
 16:("""CREATE OR REPLACE PROCEDURE training.pr_16_reset_processing()
LANGUAGE plpgsql AS $$ BEGIN UPDATE training.order_work SET processed_at=NULL; END $$;""","Сбрасываем признак обработки у всей учебной рабочей таблицы."),
 17:("""CREATE OR REPLACE PROCEDURE training.pr_17_load_order_total(p_id text)
LANGUAGE plpgsql AS $$ BEGIN
 INSERT INTO training.order_totals(order_id,order_total)
 SELECT p_id,round(sum(price+freight_value),2) FROM staging.order_items WHERE order_id=p_id
 HAVING count(*)>0 ON CONFLICT(order_id) DO UPDATE SET order_total=excluded.order_total,loaded_at=clock_timestamp();
END $$;""","Агрегируем позиции до одной строки заказа и используем UPSERT для повторной загрузки."),
 18:("""CREATE OR REPLACE PROCEDURE training.pr_18_load_customer_orders(p_customer text)
LANGUAGE plpgsql AS $$ BEGIN
 INSERT INTO training.order_work(order_id,customer_id,order_status,purchased_at)
 SELECT o.order_id,o.customer_id,o.order_status,o.purchased_at FROM staging.orders o
 JOIN staging.customers c ON c.customer_id=o.customer_id WHERE c.customer_unique_id=p_customer
 ON CONFLICT(order_id) DO NOTHING;
END $$;""","Через customers находим все заказы постоянного покупателя и загружаем их без дублей."),
 19:("""CREATE OR REPLACE PROCEDURE training.pr_19_rebuild_state_summary()
LANGUAGE plpgsql AS $$ BEGIN
 DELETE FROM training.state_summary;
 INSERT INTO training.state_summary(state,orders_count)
 SELECT c.state,count(*) FROM staging.orders o JOIN staging.customers c ON c.customer_id=o.customer_id GROUP BY c.state;
END $$;""","Полностью пересобираем агрегат: одна строка результата соответствует одному штату."),
 20:("""CREATE OR REPLACE PROCEDURE training.pr_20_refresh_month(p_month date)
LANGUAGE plpgsql AS $$ BEGIN
 INSERT INTO training.monthly_work(month_start,orders_count,revenue)
 SELECT p_month,m.orders_count,m.revenue
 FROM mart.monthly_sales m WHERE m.month=p_month
 ON CONFLICT(month_start) DO UPDATE SET orders_count=excluded.orders_count,revenue=excluded.revenue;
END $$;""","Берём согласованный месячный итог из витрины и перезаписываем одну строку через UPSERT."),
 21:("""CREATE OR REPLACE PROCEDURE training.pr_21_validate_positive_amount(p_amount numeric)
LANGUAGE plpgsql AS $$ BEGIN
 IF p_amount<0 THEN RAISE EXCEPTION 'amount must be non-negative'; END IF;
 INSERT INTO training.procedure_log(event_name,amount) VALUES('positive_amount',p_amount);
END $$;""","Сначала проверяем бизнес-правило; при корректном значении записываем сумму в журнал."),
 22:("""CREATE OR REPLACE PROCEDURE training.pr_22_require_customer(p_id text)
LANGUAGE plpgsql AS $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM mart.customer_summary WHERE customer_unique_id=p_id)
 THEN RAISE EXCEPTION 'customer % not found',p_id; END IF;
END $$;""","EXISTS проверяет наличие клиента, а понятное исключение останавливает работу при отсутствии."),
 23:("""CREATE OR REPLACE PROCEDURE training.pr_23_move_customer(p_old text,p_new text)
LANGUAGE plpgsql AS $$ BEGIN
 UPDATE training.customer_work SET customer_unique_id=p_new WHERE customer_unique_id=p_old;
EXCEPTION WHEN unique_violation THEN RAISE EXCEPTION 'customer % already exists',p_new;
END $$;""","Меняем ключ обычным UPDATE и преобразуем конфликт уникальности в понятную ошибку."),
 24:("""CREATE OR REPLACE PROCEDURE training.pr_24_archive_old_orders(p_before date)
LANGUAGE plpgsql AS $$ BEGIN
 INSERT INTO training.order_archive SELECT * FROM training.order_work
 WHERE purchased_at<p_before ON CONFLICT(order_id) DO UPDATE SET order_status=excluded.order_status;
 DELETE FROM training.order_work WHERE purchased_at<p_before;
END $$;""","Одинаковым предикатом сначала копируем старые строки в архив, затем удаляем их из рабочей таблицы."),
 25:("""CREATE OR REPLACE PROCEDURE training.pr_25_apply_discount(p_state text,p_percent numeric)
LANGUAGE plpgsql AS $$ BEGIN
 IF p_percent<0 OR p_percent>100 THEN RAISE EXCEPTION 'percent out of range'; END IF;
 UPDATE training.order_work w SET order_total=round(w.order_total*(1-p_percent/100),2)
 FROM staging.customers c WHERE c.customer_id=w.customer_id AND c.state=p_state;
END $$;""","Проверяем диапазон скидки и обновляем только заказы клиентов выбранного штата."),
 26:("""CREATE OR REPLACE PROCEDURE training.pr_26_batch_log(p_prefix text,p_amount integer)
LANGUAGE plpgsql AS $$ BEGIN
 FOR i IN 1..p_amount LOOP
  INSERT INTO training.procedure_log(message) VALUES(p_prefix||'_'||i);
 END LOOP;
END $$;""","Цикл создаёт ровно заданное число сообщений с последовательными суффиксами."),
 27:("""CREATE OR REPLACE PROCEDURE training.pr_27_process_unhandled(p_batch integer)
LANGUAGE plpgsql AS $$ BEGIN
 UPDATE training.order_work SET processed_at=clock_timestamp()
 WHERE order_id IN(SELECT order_id FROM training.order_work WHERE processed_at IS NULL ORDER BY order_id LIMIT p_batch);
END $$;""","Подзапрос выбирает ограниченный стабильный batch, а UPDATE отмечает только выбранные ключи."),
 28:("""CREATE OR REPLACE PROCEDURE training.pr_28_dynamic_clear(p_table text)
LANGUAGE plpgsql AS $$ BEGIN
 IF p_table NOT IN('procedure_log','customer_work','order_work') THEN RAISE EXCEPTION 'table is not allowed'; END IF;
 EXECUTE format('DELETE FROM training.%I',p_table);
END $$;""","Белый список ограничивает область действия, а %I безопасно форматирует имя таблицы."),
 29:("""CREATE OR REPLACE PROCEDURE training.pr_29_refresh_all()
LANGUAGE plpgsql AS $$ BEGIN
 CALL training.pr_11_refresh_order_sample(100);
 CALL training.pr_19_rebuild_state_summary();
END $$;""","Оркестратор последовательно вызывает уже готовые процедуры обновления."),
 30:("""CREATE OR REPLACE PROCEDURE training.pr_30_build_customer_snapshot(p_date date)
LANGUAGE plpgsql AS $$ BEGIN
 DELETE FROM training.customer_snapshot WHERE as_of_date=p_date;
 INSERT INTO training.customer_snapshot(as_of_date,customer_unique_id,orders_count)
 SELECT p_date,c.customer_unique_id,count(*) FROM staging.orders o
 JOIN staging.customers c ON c.customer_id=o.customer_id
 WHERE o.purchased_at<p_date+1 GROUP BY c.customer_unique_id;
END $$;""","Удаляем прежний срез этой даты и атомарно строим новый с одной строкой на покупателя."),
}
