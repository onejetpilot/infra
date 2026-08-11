import os
from pathlib import Path

import nbformat as nbf

from procedure_solutions import SOLUTIONS


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = Path(os.environ.get(
    "SQL_COURSE_OUTPUT",
    ROOT / "notebooks" / "06_Procedures_30_Tasks.ipynb",
))


tasks = [
    ("pr_01_log_message(message text)", "Добавьте сообщение в `training.procedure_log`.", "INSERT"),
    ("pr_02_log_event(event_name text, payload jsonb)", "Добавьте событие и JSON-параметры в журнал.", "Поля процедуры можно передавать прямо в VALUES."),
    ("pr_03_clear_log()", "Удалите все строки из `training.procedure_log`.", "Для небольшой учебной таблицы используйте DELETE."),
    ("pr_04_add_customer(customer_unique_id text, city text, state text)", "Добавьте клиента в `training.customer_work`.", "Явно перечисляйте колонки INSERT."),
    ("pr_05_change_customer_city(customer_unique_id text, new_city text)", "Измените город существующего клиента.", "UPDATE с точным WHERE."),
    ("pr_06_delete_customer(customer_unique_id text)", "Удалите выбранного клиента из рабочей таблицы.", "DELETE без WHERE удалит всех клиентов."),
    ("pr_07_upsert_customer(customer_unique_id text, city text, state text)", "Добавьте клиента либо обновите его город и штат.", "INSERT ... ON CONFLICT ... DO UPDATE."),
    ("pr_08_copy_customer(customer_unique_id text)", "Скопируйте выбранного клиента из `staging.customers` в `training.customer_work` без дублей.", "INSERT ... SELECT и ON CONFLICT."),
    ("pr_09_copy_state_customers(state text)", "Скопируйте всех покупателей указанного штата без дублей.", "Параметр может совпасть с именем колонки — используйте алиасы."),
    ("pr_10_count_state_customers(state text)", "Запишите в журнал количество клиентов штата.", "Сначала SELECT count(*) INTO переменную."),
    ("pr_11_refresh_order_sample(limit_rows integer)", "Полностью пересоберите `training.order_work` первыми N заказами.", "DELETE, затем INSERT ... SELECT ... LIMIT."),
    ("pr_12_load_orders_between(date_from date, date_to date)", "Добавьте заказы полуинтервала дат `[date_from, date_to)` без дублей.", "Фильтруйте timestamp диапазоном."),
    ("pr_13_update_order_status(order_id text, new_status text)", "Обновите статус заказа в рабочей таблице.", "Проверьте число изменённых строк через GET DIAGNOSTICS."),
    ("pr_14_delete_cancelled_orders()", "Удалите отменённые и недоступные заказы.", "Условие удобно выразить через IN."),
    ("pr_15_mark_processed(order_id text)", "Установите `processed_at` для заказа текущим временем.", "clock_timestamp() отражает реальное время вызова."),
    ("pr_16_reset_processing()", "Сбросьте `processed_at` у всех рабочих заказов.", "Присвойте NULL."),
    ("pr_17_load_order_total(order_id text)", "Запишите итог выбранного заказа в `training.order_totals`.", "Агрегируйте позиции до UPSERT."),
    ("pr_18_load_customer_orders(customer_unique_id text)", "Загрузите все заказы покупателя в рабочую таблицу.", "Соедините customers и orders."),
    ("pr_19_rebuild_state_summary()", "Пересоберите `training.state_summary`: штат и число заказов.", "Сначала очистка, затем агрегирующий INSERT."),
    ("pr_20_refresh_month(month_start date)", "Перезапишите месячный итог в `training.monthly_work`.", "Граница конца: month_start + interval '1 month'."),
    ("pr_21_validate_positive_amount(amount numeric)", "При отрицательной сумме выбросьте исключение, иначе запишите сумму в журнал.", "RAISE EXCEPTION и IF."),
    ("pr_22_require_customer(customer_unique_id text)", "Выбросьте исключение, если покупателя нет в mart.customer_summary.", "IF NOT EXISTS (...)."),
    ("pr_23_move_customer(old_id text, new_id text)", "Переименуйте ключ клиента; конфликт нового ключа обработайте понятным исключением.", "Обработайте unique_violation."),
    ("pr_24_archive_old_orders(before_date date)", "Перенесите старые строки из order_work в order_archive и удалите их из источника.", "Сначала INSERT, затем DELETE с одинаковым предикатом."),
    ("pr_25_apply_discount(state text, percent numeric)", "Уменьшите `order_total` рабочих заказов клиентов штата на заданный процент.", "Защититесь от процента вне 0..100."),
    ("pr_26_batch_log(prefix text, amount integer)", "Циклом добавьте amount сообщений вида prefix_1, prefix_2 и т.д.", "FOR i IN 1..amount LOOP."),
    ("pr_27_process_unhandled(batch_size integer)", "Отметьте не более batch_size необработанных заказов.", "UPDATE по подзапросу с ORDER BY и LIMIT."),
    ("pr_28_dynamic_clear(table_name text)", "Безопасно очистите одну из разрешённых training-таблиц по имени.", "Белый список плюс format('%I.%I', ...)."),
    ("pr_29_refresh_all()", "Одним вызовом выполните процедуры пересборки выборки заказов и сводки штатов.", "Процедура может вызывать другие процедуры через CALL."),
    ("pr_30_build_customer_snapshot(as_of_date date)", "Атомарно пересоберите snapshot клиентов с числом заказов не позднее даты.", "Вся последовательность должна завершаться целиком или откатываться."),
]


def md(value):
    return nbf.v4.new_markdown_cell(value)


def code(value):
    return nbf.v4.new_code_cell(value)


cells = [
    md(
        "# Процедуры PostgreSQL — 30 заданий\n\n"
        "Процедура предназначена прежде всего для выполнения действий: загрузки, обновления, "
        "удаления и организации нескольких SQL-команд в один вызываемый объект. В этом модуле "
        "мы работаем с копиями данных в схеме `training`; таблицы `raw`, `staging` и `mart` "
        "используются только как источники.\n\n"
        "Готовых решений в ноутбуке нет. После каждого задания есть ручной вызов и автоматическая проверка."
    ),
    code(
        "%load_ext sql\n"
        "%config SqlMagic.displaylimit = 50\n"
        "%sql postgresql+psycopg2://student:sqltrain2026@sql-train-db:5432/sql_train"
    ),
    md(
        "## 0. Какие данные используются\n\n"
        "Основная цепочка Olist:\n\n"
        "```text\n"
        "staging.customers (1) ──< staging.orders (1) ──< staging.order_items\n"
        "                                            └──< staging.order_payments\n"
        "```\n\n"
        "- клиент и заказ соединяются по `customer_id`;\n"
        "- заказы одного реального покупателя объединяет `customer_unique_id`;\n"
        "- заказ и позиции соединяются по `order_id`;\n"
        "- изменять исходные таблицы нельзя;\n"
        "- все изменения выполняются в `training.customer_work`, `training.order_work` и других учебных таблицах."
    ),
    code(
        "%%sql\n"
        "SELECT table_name, column_name, data_type\n"
        "FROM information_schema.columns\n"
        "WHERE table_schema = 'training'\n"
        "  AND table_name IN ('procedure_log', 'customer_work', 'order_work')\n"
        "ORDER BY table_name, ordinal_position;"
    ),
    md(
        "## 1. Чем процедура отличается от функции\n\n"
        "| Функция | Процедура |\n"
        "|---|---|\n"
        "| Вызывается в выражении: `SELECT f(...)` | Вызывается отдельной командой: `CALL p(...)` |\n"
        "| Обязана объявить возвращаемый тип | Обычно сообщает результат через изменения данных или OUT-параметры |\n"
        "| Хороша для вычислений и наборов строк | Хороша для ETL и последовательности команд |\n"
        "| Не предназначена для управления транзакцией | При подходящем способе вызова может управлять транзакцией |\n\n"
        "Процедура не является «функцией без RETURN». Выбирайте её, когда главный результат — "
        "изменённое состояние базы."
    ),
    md(
        "## 2. Базовый синтаксис\n\n"
        "```sql\n"
        "CREATE OR REPLACE PROCEDURE training.demo_write_log(p_message text)\n"
        "LANGUAGE plpgsql\n"
        "AS $$\n"
        "BEGIN\n"
        "    INSERT INTO training.procedure_log(message)\n"
        "    VALUES (p_message);\n"
        "END;\n"
        "$$;\n\n"
        "CALL training.demo_write_log('hello');\n"
        "```\n\n"
        "`p_` перед именем параметра — полезное соглашение: оно предотвращает неоднозначность "
        "между параметром и одноимённой колонкой. `CREATE OR REPLACE` позволяет исправлять тело "
        "процедуры повторным выполнением ячейки."
    ),
    md(
        "## 3. Переменные и диагностика\n\n"
        "Переменные объявляются между `DECLARE` и `BEGIN`. Значение запроса записывают через "
        "`SELECT ... INTO`. После `INSERT`, `UPDATE` или `DELETE` количество затронутых строк "
        "можно получить командой `GET DIAGNOSTICS v_rows = ROW_COUNT`. Это помогает отличить "
        "успешную команду, которая ничего не нашла, от реального изменения данных."
    ),
    md(
        "## 4. Исключения и атомарность\n\n"
        "`RAISE EXCEPTION` прерывает выполнение. Если исключение не перехвачено, изменения "
        "текущей транзакции откатываются. Блок `EXCEPTION WHEN unique_violation THEN ...` "
        "позволяет обработать конкретную ошибку, но не следует скрывать все ошибки через "
        "`WHEN OTHERS` без веской причины.\n\n"
        "Перед каждой процедурой определите: какие таблицы она меняет, что произойдёт при "
        "повторном вызове и должна ли операция быть идемпотентной."
    ),
    md(
        "## 5. Порядок выполнения задания\n\n"
        "1. Посмотрите структуру целевой и исходной таблиц.\n"
        "2. Выполните изменяющую команду вручную внутри `BEGIN; ... ROLLBACK;`.\n"
        "3. Продумайте повторный вызов, NULL и отсутствие строки.\n"
        "4. Создайте процедуру с точной сигнатурой.\n"
        "5. Вызовите её через `CALL` и проверьте результат отдельным SELECT.\n"
        "6. Запустите автоматическую проверку — она сама восстанавливает учебную песочницу."
    ),
]

for number, (signature, prompt, hint) in enumerate(tasks, 1):
    if number == 11:
        cells.append(md("## Уровень 2 — пакетные загрузки\n\nТеперь одна процедура выполняет несколько согласованных действий и должна корректно работать повторно."))
    if number == 21:
        cells.append(md("## Уровень 3 — валидация, исключения и orchestration\n\nЗдесь особенно важны атомарность, безопасный динамический SQL и понятные ошибки."))
    cells.extend([
        md(
            f"### Задание {number}. `training.{signature}`\n\n"
            f"**Результат:** {prompt}\n\n"
            "**Как подойти:** сначала составьте отдельные SQL-команды и проверьте их в "
            "`BEGIN/ROLLBACK`; затем перенесите их в `BEGIN ... END` процедуры. После вызова "
            "проверьте именно изменившиеся строки, а не только отсутствие ошибки.\n\n"
            "**Частые ошибки:** нет схемы `training`, перепутан `SELECT` и `CALL`, параметр "
            "конфликтует с колонкой, отсутствует `WHERE`, повторный вызов создаёт дубли.\n\n"
            f"<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"
        ),
        code(
            "%%sql\n"
            f"-- Требуемая сигнатура: training.{signature}\n"
            "-- CREATE OR REPLACE PROCEDURE ...\n"
        ),
        code(
            "%%sql\n"
            "-- Ручная проверка:\n"
            "-- CALL training.pr_...(...);\n"
            "-- SELECT ... FROM training....;\n"
        ),
        *([md(
            "<details><summary><strong>Эталонное решение и разбор</strong></summary>\n\n"
            "Откройте блок после самостоятельной попытки.\n\n"
            f"```sql\n{SOLUTIONS[number][0]}\n```\n\n"
            f"**Что делаем:** {SOLUTIONS[number][1]}\n\n"
            "Выполните DDL, вызовите процедуру через CALL и проверьте изменённые строки отдельным SELECT.\n\n"
            "</details>"
        )] if number in SOLUTIONS else []),
        code(
            "%%sql\n"
            f"SELECT * FROM training.run_checks('procedures', {number});"
        ),
    ])

cells.extend([
    md("## Прогресс\n\nПроверка каждого задания выполняется независимо на восстановленной учебной песочнице."),
    code(
        "%%sql\n"
        "SELECT task_no, tests_passed, tests_total, completed, checked_at\n"
        "FROM training.progress\n"
        "WHERE module_name = 'procedures'\n"
        "ORDER BY task_no;"
    ),
])

notebook = nbf.v4.new_notebook(
    cells=cells,
    metadata={"kernelspec": {
        "display_name": "Python 3 (ipykernel)",
        "language": "python",
        "name": "python3",
    }},
)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(notebook, OUTPUT)
print(OUTPUT)
