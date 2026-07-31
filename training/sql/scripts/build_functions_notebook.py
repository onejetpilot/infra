import os
from pathlib import Path

import nbformat as nbf


SCRIPT_PATH = Path(__file__).resolve()
COURSE_ROOT = SCRIPT_PATH.parent.parent
OUTPUT = Path(
    os.environ.get(
        "SQL_COURSE_OUTPUT",
        COURSE_ROOT / "notebooks" / "01_Functions_30_Tasks.ipynb",
    )
)


tasks = [
    ("fn_01_full_name(first_name text, last_name text) → text", "Очистите оба аргумента функцией trim и соедините непустые части одним пробелом.", "Проверьте поведение concat_ws с NULL."),
    ("fn_02_add_tax(amount numeric, tax_percent numeric) → numeric", "Верните сумму с налогом, округлённую до двух знаков.", "Формула: amount * (1 + tax_percent / 100)."),
    ("fn_03_safe_int(value text) → integer", "Преобразуйте текст в integer. Для NULL и некорректного текста возвращайте NULL, не ошибку.", "Понадобится блок EXCEPTION в PL/pgSQL."),
    ("fn_04_order_year(value timestamp) → integer", "Верните год переданной временной метки.", "Подумайте об EXTRACT и явном приведении типа."),
    ("fn_05_delivery_days(order_id text) → integer", "Найдите заказ в staging.orders и верните число календарных дней от покупки до доставки.", "SELECT ... INTO; если доставка отсутствует, результат должен быть NULL."),
    ("fn_06_order_total(order_id text) → numeric", "Посчитайте сумму price + freight_value по всем позициям заказа и округлите до двух знаков.", "Агрегируйте staging.order_items внутри SQL-функции."),
    ("fn_07_customer_orders(customer_unique_id text) → bigint", "Верните orders_count из mart.customer_summary. Для неизвестного клиента верните 0.", "Используйте COALESCE вокруг результата подзапроса."),
    ("fn_08_payment_label(amount numeric) → text", "Классифицируйте платёж: меньше 100 — small, от 100 до 499.99 — medium, от 500 — large.", "Условия CASE проверяются сверху вниз."),
    ("fn_09_is_late(order_id text) → boolean", "Верните признак delivered_late из mart.order_finance.", "Не пересчитывайте уже готовый признак."),
    ("fn_10_state_order_count(state text) → bigint", "Посчитайте все заказы покупателей указанного штата.", "Соедините staging.orders и staging.customers по customer_id."),
    ("fn_11_orders_between(date_from date, date_to date) → TABLE(order_id text, purchased_at timestamp)", "Верните заказы полуинтервала [date_from, date_to).", "Для табличной SQL-функции используйте RETURNS TABLE."),
    ("fn_12_top_customers(limit_rows integer DEFAULT 10) → TABLE(customer_unique_id text, orders_count bigint, lifetime_value numeric)", "Верните покупателей с максимальным lifetime_value, затем orders_count.", "LIMIT может принимать аргумент функции."),
    ("fn_13_category_revenue(category_name text) → numeric", "Верните суммарную выручку категории из mart.product_sales.", "Для отсутствующей категории верните 0."),
    ("fn_14_order_status_summary() → TABLE(order_status text, orders_count bigint)", "Верните количество заказов по каждому статусу.", "Не забудьте GROUP BY и стабильный порядок результата."),
    ("fn_15_customer_ltv(customer_unique_id text) → numeric", "Верните lifetime_value покупателя.", "Неизвестный покупатель должен дать 0, а не отсутствие строки."),
    ("fn_16_product_dimensions(product_id text) → jsonb", "Верните JSON с product_id, weight_g, length_cm, height_cm и width_cm.", "Удобны jsonb_build_object или to_jsonb строки."),
    ("fn_17_normalize_city(city text) → text", "Удалите пробелы по краям, замените последовательности пробелов одним и приведите строку к нижнему регистру.", "regexp_replace(..., '\\s+', ' ', 'g')."),
    ("fn_18_days_from_purchase(order_id text, as_of_date date DEFAULT current_date) → integer", "Посчитайте дни от даты покупки до заданной даты отсчёта.", "Значение по умолчанию указывается в объявлении аргумента."),
    ("fn_19_percent_change(old_value numeric, new_value numeric) → numeric", "Верните процентное изменение с двумя знаками. При old_value=0 или NULL верните NULL.", "NULLIF защищает от деления на ноль."),
    ("fn_20_existing_orders(order_ids text[]) → TABLE(order_id text)", "Верните только существующие order_id из переданного массива.", "Сравнение с массивом: = ANY(...)."),
    ("fn_21_monthly_revenue(year_num integer) → TABLE(month date, revenue numeric)", "Верните месяцы и выручку выбранного года из mart.monthly_sales.", "Фильтруйте по диапазону дат, а не по текстовому представлению."),
    ("fn_22_seller_rank(seller_id text) → bigint", "Рассчитайте ранг продавца по суммарной цене товаров; максимальная выручка получает ранг 1.", "Сначала агрегируйте продавцов, затем примените dense_rank."),
    ("fn_23_customer_profile(customer_unique_id text) → jsonb", "Верните JSON ровно с ключами customer_unique_id, orders_count и lifetime_value.", "to_jsonb подзапроса сохраняет имена колонок."),
    ("fn_24_search_orders(filters jsonb) → TABLE(order_id text)", "Поддержите необязательные JSON-фильтры status и state. Отсутствующий ключ не должен ограничивать результат.", "Извлечение текста: filters ->> 'status'."),
    ("fn_25_table_row_count(schema_name text, table_name text) → bigint", "Посчитайте строки произвольной таблицы безопасным динамическим SQL.", "Идентификаторы подставляйте через format('%I.%I', ...), не конкатенацией."),
    ("fn_26_audit_event(event_name text, payload jsonb) → bigint", "Добавьте запись в training.function_audit и верните audit_id. Объявите функцию VOLATILE.", "INSERT ... RETURNING audit_id INTO переменную."),
    ("fn_27_order_count() → bigint", "Верните число заказов staging.orders и явно объявите функцию STABLE.", "Проверка контролирует не только значение, но и volatility."),
    ("fn_28_distance_km(lat1 numeric, lon1 numeric, lat2 numeric, lon2 numeric) → numeric", "Рассчитайте расстояние по формуле haversine с радиусом Земли 6371 км.", "PostgreSQL sin/cos работают с радианами; используйте radians()."),
    ("fn_29_cohort_retention(cohort_month date, month_offset integer) → numeric", "Верните процент клиентов когорты первой покупки, совершивших заказ через month_offset месяцев.", "Сначала определите первый месяц каждого клиента, затем активность нужного месяца."),
    ("fn_30_customer_segment(customer_unique_id text) → text", "Сегментируйте клиента: VIP — верхний клиент по LTV (не ниже максимального LTV), loyal — больше одного заказа, regular — один заказ, unknown — клиента нет.", "Получите orders_count, lifetime_value и максимальный LTV в PL/pgSQL."),
]


def md(text):
    return nbf.v4.new_markdown_cell(text)


def code(text):
    return nbf.v4.new_code_cell(text)


cells = [
    md(
        "# Функции PostgreSQL — 30 заданий\n\n"
        "Этот ноутбук устроен как учебник-практикум. Сначала прочитайте теорию и выполните "
        "небольшие демонстрационные примеры, затем переходите к заданиям. Решений заданий "
        "здесь нет: каждая ваша функция автоматически проверяется на реальных данных Olist.\n\n"
        "Создавайте объекты строго в схеме `training` и точно соблюдайте указанную сигнатуру."
    ),
    code(
        "%load_ext sql\n"
        "%config SqlMagic.displaylimit = 50\n"
        "%sql postgresql+psycopg2://student:sqltrain2026@sql-train-db:5432/sql_train"
    ),
    md(
        "## 0. Схема учебных данных Olist\n\n"
        "Olist — данные бразильского маркетплейса. Центральная сущность модели — заказ. "
        "Один покупатель создаёт много заказов, один заказ содержит несколько товарных "
        "позиций и платежей, а товарные позиции связывают заказ с товарами и продавцами.\n\n"
        "Данные проходят три слоя:\n\n"
        "| Схема | Назначение | Когда использовать |\n"
        "|---|---|---|\n"
        "| `raw` | CSV почти без преобразований; большинство полей имеют тип `text` | Для знакомства с исходными данными, но не для заданий курса |\n"
        "| `staging` | Очищенные названия колонок и правильные типы `timestamp`, `numeric`, `integer` | Для детальных строк заказов, товаров, платежей и клиентов |\n"
        "| `mart` | Готовые агрегаты и рассчитанные признаки | Когда условие просит готовую выручку, LTV, просрочку или месячный итог |\n\n"
        "В заданиях нельзя автоматически заменять `staging` на `raw`: названия и типы "
        "колонок у этих слоёв различаются."
    ),
    md(
        "### Основные связи\n\n"
        "```text\n"
        "staging.customers (1) ──< staging.orders (1) ──< staging.order_items >── (1) staging.products\n"
        "                                      │                    │\n"
        "                                      │                    └──────────────> staging.sellers\n"
        "                                      ├──< staging.order_payments\n"
        "                                      └──< staging.order_reviews\n"
        "```\n\n"
        "Ключи соединения:\n\n"
        "| Левая таблица | Правая таблица | Условие `JOIN` |\n"
        "|---|---|---|\n"
        "| `staging.customers c` | `staging.orders o` | `o.customer_id = c.customer_id` |\n"
        "| `staging.orders o` | `staging.order_items oi` | `oi.order_id = o.order_id` |\n"
        "| `staging.orders o` | `staging.order_payments p` | `p.order_id = o.order_id` |\n"
        "| `staging.orders o` | `staging.order_reviews r` | `r.order_id = o.order_id` |\n"
        "| `staging.order_items oi` | `staging.products pr` | `pr.product_id = oi.product_id` |\n"
        "| `staging.order_items oi` | `staging.sellers s` | `s.seller_id = oi.seller_id` |\n\n"
        "`customer_id` относится к записи клиента конкретного заказа. "
        "`customer_unique_id` объединяет заказы одного реального покупателя — именно его "
        "используют для подсчёта повторных покупок и LTV."
    ),
    md(
        "### Что хранится в основных таблицах\n\n"
        "- `staging.orders`: одна строка на заказ; статус и даты покупки, одобрения и доставки.\n"
        "- `staging.order_items`: одна строка на позицию заказа; товар, продавец, цена и доставка.\n"
        "- `staging.customers`: покупатель, его постоянный идентификатор, город и штат.\n"
        "- `staging.products`: категория и физические размеры товара.\n"
        "- `staging.order_payments`: платежи заказа; у одного заказа их может быть несколько.\n"
        "- `mart.order_finance`: одна строка на заказ с финансовыми итогами и `delivered_late`.\n"
        "- `mart.customer_summary`: одна строка на покупателя с количеством заказов и LTV.\n"
        "- `mart.product_sales`: продажи, агрегированные по товару.\n"
        "- `mart.monthly_sales`: месячные показатели заказов и выручки.\n\n"
        "Важно понимать гранулярность. Соединение двух таблиц вида «один-ко-многим» может "
        "размножить строки. Например, если сразу присоединить к заказу и позиции, и платежи, "
        "итоги могут задвоиться. Перед `JOIN` всегда спрашивайте: чему равна одна строка "
        "каждой таблицы?"
    ),
    code(
        "%%sql\n"
        "-- Список доступных учебных таблиц.\n"
        "SELECT table_schema, table_name\n"
        "FROM information_schema.tables\n"
        "WHERE table_schema IN ('raw', 'staging', 'mart')\n"
        "  AND table_type = 'BASE TABLE'\n"
        "ORDER BY table_schema, table_name;"
    ),
    code(
        "%%sql\n"
        "-- Универсальный способ посмотреть колонки и типы нужной таблицы.\n"
        "-- Замените staging.orders на таблицу, с которой собираетесь работать.\n"
        "SELECT column_name, data_type, is_nullable\n"
        "FROM information_schema.columns\n"
        "WHERE table_schema = 'staging'\n"
        "  AND table_name = 'orders'\n"
        "ORDER BY ordinal_position;"
    ),
    code(
        "%%sql\n"
        "-- Несколько строк помогают понять данные до написания функции.\n"
        "SELECT *\n"
        "FROM staging.orders\n"
        "LIMIT 5;"
    ),
    md(
        "## 1. Что такое функция\n\n"
        "Функция — объект базы данных, которому передают аргументы и который возвращает "
        "значение или набор строк. В отличие от скопированного фрагмента SQL, функция имеет "
        "имя, фиксированный контракт и может вызываться из `SELECT`, `WHERE`, `JOIN` и других "
        "функций.\n\n"
        "Контракт функции состоит из четырёх частей:\n\n"
        "1. имя, например `training.calculate_discount`;\n"
        "2. входные аргументы и их типы;\n"
        "3. возвращаемый тип после `RETURNS`;\n"
        "4. реализация и язык (`sql` или `plpgsql`).\n\n"
        "PostgreSQL различает функции не только по имени, но и по типам аргументов. "
        "`f(integer)` и `f(text)` — две разные сигнатуры."
    ),
    md(
        "## 2. SQL-функция: когда достаточно одного запроса\n\n"
        "Если результат можно выразить одним `SELECT`, выбирайте `LANGUAGE sql`. Такой код "
        "короче и обычно легче оптимизируется планировщиком.\n\n"
        "Пример ниже не является решением заданий курса:"
    ),
    code(
        "%%sql\n"
        "CREATE OR REPLACE FUNCTION training.demo_discount(\n"
        "    price numeric,\n"
        "    discount_percent numeric\n"
        ")\n"
        "RETURNS numeric\n"
        "LANGUAGE sql\n"
        "IMMUTABLE\n"
        "AS $$\n"
        "    SELECT round(price * (1 - discount_percent / 100), 2);\n"
        "$$;\n"
        "\n"
        "SELECT training.demo_discount(1000, 15) AS discounted_price;"
    ),
    md(
        "Разберите пример по строкам:\n\n"
        "- `CREATE OR REPLACE` позволяет повторно выполнить ячейку;\n"
        "- аргументы видны внутри тела по именам `price` и `discount_percent`;\n"
        "- `RETURNS numeric` обещает вернуть одно число;\n"
        "- после `AS $$ ... $$` находится обычный SQL-запрос;\n"
        "- `IMMUTABLE` означает, что одинаковые аргументы всегда дают одинаковый результат.\n\n"
        "Если фактический результат нельзя привести к типу после `RETURNS`, функция не "
        "создастся или завершится ошибкой при вызове."
    ),
    md(
        "## 3. PL/pgSQL: переменные, ветвления и исключения\n\n"
        "`LANGUAGE plpgsql` нужен, когда одного запроса недостаточно. Тело функции делится "
        "на необязательный `DECLARE` и обязательный блок `BEGIN ... END`.\n\n"
        "Основные команды:\n\n"
        "- `SELECT ... INTO variable` — записать результат запроса в переменную;\n"
        "- `IF / ELSIF / ELSE` — выполнить разные ветви;\n"
        "- `RETURN value` — вернуть скалярное значение;\n"
        "- `RETURN QUERY SELECT ...` — добавить строки в табличный результат;\n"
        "- `EXCEPTION WHEN ...` — обработать ожидаемую ошибку."
    ),
    code(
        "%%sql\n"
        "CREATE OR REPLACE FUNCTION training.demo_temperature_label(value numeric)\n"
        "RETURNS text\n"
        "LANGUAGE plpgsql\n"
        "IMMUTABLE\n"
        "AS $$\n"
        "BEGIN\n"
        "    IF value IS NULL THEN\n"
        "        RETURN 'unknown';\n"
        "    ELSIF value < 0 THEN\n"
        "        RETURN 'freezing';\n"
        "    ELSIF value < 20 THEN\n"
        "        RETURN 'cold';\n"
        "    ELSE\n"
        "        RETURN 'warm';\n"
        "    END IF;\n"
        "END;\n"
        "$$;\n"
        "\n"
        "SELECT training.demo_temperature_label(-5),\n"
        "       training.demo_temperature_label(25),\n"
        "       training.demo_temperature_label(NULL);"
    ),
    md(
        "## 4. NULL — это не пустая строка и не ноль\n\n"
        "`NULL` означает отсутствие известного значения. Сравнение `value = NULL` никогда "
        "не даёт `true`; используйте `IS NULL`. Арифметика с NULL обычно возвращает NULL. "
        "Для подстановки значения применяйте `COALESCE(value, replacement)`, а для защиты "
        "от деления на ноль — `NULLIF(denominator, 0)`.\n\n"
        "Перед написанием функции явно решите, что она должна делать при NULL, неизвестном "
        "идентификаторе и пустом наборе строк."
    ),
    md(
        "## 5. Скалярный и табличный результат\n\n"
        "`RETURNS integer` возвращает одно значение. Для нескольких колонок и строк используйте "
        "`RETURNS TABLE(column_name type, ...)`. В SQL-функции последним выражением должен быть "
        "запрос с тем же числом колонок и совместимыми типами.\n\n"
        "Пример формы табличной функции:\n\n"
        "```sql\n"
        "CREATE FUNCTION training.demo_items(min_price numeric)\n"
        "RETURNS TABLE(item_id text, price numeric)\n"
        "LANGUAGE sql\n"
        "AS $$\n"
        "    SELECT product_id, price\n"
        "    FROM staging.order_items\n"
        "    WHERE price >= min_price;\n"
        "$$;\n"
        "```\n\n"
        "Табличную функцию вызывают в `FROM`: "
        "`SELECT * FROM training.demo_items(100);`."
    ),
    md(
        "## 6. Как выполнять каждое задание\n\n"
        "1. Перепишите сигнатуру и выделите входы и выход.\n"
        "2. Сформулируйте результат обычным `SELECT` без функции.\n"
        "3. Проверьте этот SELECT на двух-трёх значениях.\n"
        "4. Выберите `LANGUAGE sql` или `plpgsql`.\n"
        "5. Оберните рабочую логику в `CREATE OR REPLACE FUNCTION`.\n"
        "6. Вручную вызовите функцию.\n"
        "7. Только после этого запускайте ячейку `training.run_checks`.\n\n"
        "`ERROR` означает, что объект отсутствует или вызов завершился SQL-ошибкой. `FAIL` "
        "означает, что функция выполнилась, но результат отличается от ожидаемого. `PASS` — "
        "проверка пройдена."
    ),
]

for number, (signature, prompt, hint) in enumerate(tasks, start=1):
    if number == 11:
        cells.append(md(
            "## Уровень 2 — табличные функции и составные типы\n\n"
            "Здесь функции начинают возвращать наборы строк, принимать параметры по умолчанию, "
            "массивы и JSON. Сначала всегда проверяйте форму обычного SELECT: имена, порядок и "
            "типы его колонок должны совпадать с `RETURNS TABLE`."
        ))
    if number == 21:
        cells.append(md(
            "## Уровень 3 — продвинутые функции\n\n"
            "### Volatility\n\n"
            "- `IMMUTABLE`: результат зависит только от аргументов;\n"
            "- `STABLE`: внутри одного запроса результат стабилен, но функция может читать таблицы;\n"
            "- `VOLATILE`: функция может изменять данные или возвращать разные результаты.\n\n"
            "### Динамический SQL\n\n"
            "Используйте `EXECUTE format(...)`. Значения передавайте через `USING`, а имена схем, "
            "таблиц и колонок форматируйте спецификатором `%I`. Конкатенация пользовательского "
            "ввода в SQL создаёт риск SQL injection."
        ))

    cells.extend(
        [
            md(
                f"### Задание {number}. `{signature}`\n\n"
                f"**Что нужно получить**\n\n{prompt}\n\n"
                "**Порядок работы**\n\n"
                "1. Сначала напишите и выполните обычный SELECT, который вычисляет нужный результат.\n"
                "2. Проверьте тип результата через `pg_typeof(...)`.\n"
                "3. Создайте функцию в схеме `training` с указанным именем и аргументами.\n"
                "4. Вручную вызовите её хотя бы для нормального и граничного значения.\n"
                "5. Запустите автоматическую проверку в следующей ячейке.\n\n"
                "**Частые причины ошибки:** неверный возвращаемый тип, отсутствие схемы "
                "`training`, другая сигнатура, неправильная обработка NULL или границы диапазона.\n\n"
                f"<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"
            ),
            code(
                "%%sql\n"
                f"-- Требуемая сигнатура:\n-- training.{signature}\n\n"
                "-- Шаг 1. Сначала проверьте здесь обычный SELECT.\n"
                "-- Шаг 2. Затем замените его на CREATE OR REPLACE FUNCTION.\n"
            ),
            code(
                "%%sql\n"
                "-- Выполните ручной вызов вашей функции здесь.\n"
                "-- SELECT training.fn_...(...);\n"
            ),
            code(
                "%%sql\n"
                f"SELECT * FROM training.run_checks('functions', {number});"
            ),
        ]
    )

cells.extend(
    [
        md("## Прогресс\n\n`completed = true` означает, что последняя попытка прошла все тесты задания."),
        code(
            "%%sql\n"
            "SELECT task_no, tests_passed, tests_total, completed, checked_at\n"
            "FROM training.progress\n"
            "WHERE module_name = 'functions'\n"
            "ORDER BY task_no;"
        ),
    ]
)

notebook = nbf.v4.new_notebook(
    cells=cells,
    metadata={
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3",
        }
    },
)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(notebook, OUTPUT)
print(OUTPUT)
