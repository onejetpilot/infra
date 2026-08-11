import os
from pathlib import Path

import nbformat as nbf
from deduplication_solutions import SOLUTIONS


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = Path(os.environ.get(
    "SQL_COURSE_OUTPUT",
    ROOT / "notebooks" / "08_Deduplication_30_Tasks.ipynb",
))

tasks = [
    ("dq_01", "Найдите повторяющиеся `customer_unique_id` в `staging.customers`; верните ключ и `rows_count`.", "GROUP BY + HAVING count(*) > 1"),
    ("dq_02", "Найдите дубли `order_id` в `raw.orders`; верните ключ и `rows_count`.", "Сначала измерьте дубли, даже если ожидаете их отсутствие."),
    ("dq_03", "Верните уникальный список штатов клиентов в колонке `state`.", "DISTINCT удаляет полностью одинаковые значения."),
    ("dq_04", "Оставьте по одной строке геолокации на каждую пару `(zip_code_prefix, city)`.", "Требуется детерминированный выбор строки."),
    ("dq_05", "Оставьте по одному клиенту на `customer_unique_id`, выбирая минимальный `customer_id`.", "DISTINCT ON требует согласованного ORDER BY."),
    ("dq_06", "Пронумеруйте строки клиентов внутри `customer_unique_id`; верните все колонки и `rn`.", "row_number() over(partition by ... order by ...)"),
    ("dq_07", "Верните только лишние записи клиентов, то есть строки с `rn > 1`.", "Сначала окно в CTE, затем фильтр снаружи."),
    ("dq_08", "Для каждого `order_id` оставьте платёж с максимальным `payment_value`.", "Добавьте второй ключ сортировки при равенстве."),
    ("dq_09", "Для каждого заказа и товара оставьте одну позицию с минимальным `order_item_id`.", "Естественный ключ здесь составной."),
    ("dq_10", "Оставьте один отзыв на заказ: самый поздний по `answered_at`.", "NULLS LAST делает выбор понятным."),
    ("dq_11", "Покажите группы полностью одинаковых строк `duplicate_lab`; верните бизнес-поля и `rows_count`.", "Группировать нужно по всем бизнес-полям, кроме технического id."),
    ("dq_12", "Верните уникальные `business_key, value, updated_at, is_deleted, source` из duplicate_lab.", "DISTINCT подходит для полных дублей."),
    ("dq_13", "Оставьте последнюю версию по `business_key`; верните исходные колонки выбранной строки.", "При одинаковом времени используйте больший ingest_id."),
    ("dq_14", "Оставьте первую пришедшую версию по `business_key`; верните исходные колонки.", "Минимальный ingest_id имитирует first-write-wins."),
    ("dq_15", "Оставьте по ключу строку с непустым `value`, затем самую свежую; верните исходные колонки.", "CASE или сортировка по (value IS NULL)."),
    ("dq_16", "Верните `business_key, distinct_values_count` для ключей с несколькими различными непустыми value.", "count(DISTINCT value) FILTER (...)"),
    ("dq_17", "Верните `business_key, versions_count, first_updated_at, last_updated_at`.", "Агрегаты после GROUP BY."),
    ("dq_18", "Одной строкой верните `total_rows, distinct_rows` для полных бизнес-строк duplicate_lab.", "Два scalar subquery либо условная агрегация."),
    ("dq_19", "Одной строкой верните `duplicate_pct` — долю лишних строк относительно уникальных business_key.", "duplicates = total - distinct business keys."),
    ("dq_20", "Верните `business_key, latest_rows_count` для неоднозначных последних версий.", "Сначала max(date), затем подсчёт строк на этой дате."),
    ("dq_21", "Дедуплицируйте клиентов, предпочитая заполненные city и state, затем минимальный customer_id.", "Выразите качество строки в ORDER BY."),
    ("dq_22", "Дедуплицируйте геолокацию по zip-коду, выбрав координаты наиболее частой пары latitude/longitude.", "Сначала частота координат, затем ранжирование."),
    ("dq_23", "Дедуплицируйте товары по product_id, предпочитая наиболее полную строку.", "Посчитайте количество NOT NULL атрибутов."),
    ("dq_24", "Верните канонический платёж заказа и одновременно сумму всех платежей заказа.", "Оконные sum и row_number можно рассчитать вместе."),
    ("dq_25", "Найдите потенциально повторные отзывы с одинаковым order_id, score и нормализованным message.", "lower(trim(...)) и обработка NULL."),
    ("dq_26", "Верните `ingest_id, canonical_ingest_id`; канонической считается последняя версия ключа.", "Оконный first_value помогает назначить каноническую строку."),
    ("dq_27", "Верните по `business_key` массив `ingest_ids` в порядке возрастания.", "array_agg с сортировкой."),
    ("dq_28", "Верните исходные колонки последних версий, исключив ключи, чья последняя версия — tombstone.", "Сначала выбрать последнюю версию, только затем фильтровать удалённые."),
    ("dq_29", "Верните исходные строки новее watermark `duplicate_lab`.", "Сравнивайте пару (updated_at, ingest_id), а не только timestamp."),
    ("dq_30", "Одной строкой верните `total_rows, unique_keys, duplicate_rows, conflict_keys, duplicate_pct`.", "Соберите метрики отдельными CTE и соедините в одну строку."),
]


def md(value):
    return nbf.v4.new_markdown_cell(value)


def code(value):
    return nbf.v4.new_code_cell(value)


cells = [
    md(
        "# Дедупликация SQL — 30 заданий\n\n"
        "Дедупликация — это не команда «удалить одинаковое». Сначала определяется бизнес-ключ, "
        "затем правило выбора канонической записи, способ обработки конфликтов и контрольные "
        "метрики. В заданиях вы создаёте представления `training.dq_01`…`training.dq_30`; "
        "исходные данные не изменяются, готовые решения не публикуются."
    ),
    code(
        "%load_ext sql\n"
        "%config SqlMagic.displaylimit = 50\n"
        "%sql postgresql+psycopg2://student:sqltrain2026@sql-train-db:5432/sql_train"
    ),
    md(
        "## 0. Модель данных\n\n"
        "В Olist встречаются разные уровни уникальности:\n\n"
        "| Таблица | Гранулярность | Кандидат бизнес-ключа |\n"
        "|---|---|---|\n"
        "| `staging.orders` | заказ | `order_id` |\n"
        "| `staging.order_items` | позиция заказа | `(order_id, order_item_id)` |\n"
        "| `staging.order_payments` | часть платежа | `(order_id, payment_sequence)` |\n"
        "| `staging.customers` | запись клиента заказа | `customer_id` |\n"
        "| `staging.order_reviews` | отзыв | зависит от бизнес-правила |\n"
        "| `staging.geolocation` | координата почтового индекса | уникальность не гарантируется |\n\n"
        "`customer_unique_id` намеренно повторяется: один реальный покупатель может иметь "
        "несколько заказов. Повтор значения ещё не доказывает ошибку."
    ),
    code(
        "%%sql\n"
        "SELECT table_name, column_name, data_type\n"
        "FROM information_schema.columns\n"
        "WHERE table_schema = 'staging'\n"
        "  AND table_name IN ('customers','orders','order_items','order_payments','order_reviews','geolocation')\n"
        "ORDER BY table_name, ordinal_position;"
    ),
    md(
        "## 1. Четыре разных ситуации\n\n"
        "1. **Полный дубль** — совпадают все бизнес-поля.\n"
        "2. **Повтор ключа** — ключ одинаков, остальные значения могут различаться.\n"
        "3. **Версия** — более новая строка законно заменяет старую.\n"
        "4. **Конфликт** — несколько строк претендуют на каноническую, но правила выбора нет.\n\n"
        "Прежде чем писать `DISTINCT`, сформулируйте, какая из этих ситуаций перед вами."
    ),
    md(
        "## 2. Инструменты дедупликации\n\n"
        "- `GROUP BY ... HAVING count(*) > 1` измеряет группы повторов;\n"
        "- `DISTINCT` удаляет полностью одинаковые выбранные строки;\n"
        "- `DISTINCT ON (key)` оставляет первую строку согласно `ORDER BY` (PostgreSQL);\n"
        "- `row_number()` даёт явный номер каждой версии внутри ключа;\n"
        "- `rank()` сохраняет ничьи и поэтому не всегда даёт одну строку;\n"
        "- агрегаты позволяют сохранить происхождение: `array_agg(id)` и количество версий."
    ),
    code(
        "%%sql\n"
        "-- Демонстрационный пример, не являющийся решением задания.\n"
        "WITH demo(id, business_key, updated_at) AS (\n"
        "    VALUES (1, 'A', DATE '2024-01-01'),\n"
        "           (2, 'A', DATE '2024-02-01'),\n"
        "           (3, 'B', DATE '2024-01-15')\n"
        ")\n"
        "SELECT *,\n"
        "       row_number() OVER (\n"
        "           PARTITION BY business_key\n"
        "           ORDER BY updated_at DESC, id DESC\n"
        "       ) AS rn\n"
        "FROM demo;"
    ),
    md(
        "## 3. Почему сортировка должна быть детерминированной\n\n"
        "Если две версии имеют одинаковую дату, `ORDER BY updated_at DESC` не определяет "
        "победителя. Добавьте стабильный tie-breaker: технический идентификатор, приоритет "
        "источника или другое согласованное поле. Без этого результат может меняться между запусками."
    ),
    md(
        "## 4. Безопасный рабочий процесс\n\n"
        "1. Назовите гранулярность результата.\n"
        "2. Запишите бизнес-ключ.\n"
        "3. Посчитайте повторы и конфликты до преобразования.\n"
        "4. Определите правило победителя и tie-breaker.\n"
        "5. Создайте представление с точным набором колонок.\n"
        "6. Проверьте, что ключ результата уникален.\n"
        "7. Сравните количество строк до и после.\n"
        "8. Запустите автоматическую проверку."
    ),
]

for number, (view_name, prompt, hint) in enumerate(tasks, 1):
    if number == 11:
        cells.append(md("## Уровень 2 — версии и конфликты\n\nИспользуется специально подготовленная таблица `training.duplicate_lab` с контролируемыми дублями."))
    if number == 21:
        cells.append(md("## Уровень 3 — промышленные правила\n\nТеперь учитываются качество записи, происхождение, tombstone и инкрементальный watermark."))
    cells.extend([
        md(
            f"### Задание {number}. Представление `training.{view_name}`\n\n"
            f"**Что получить:** {prompt}\n\n"
            "**Порядок работы:** сначала выполните запрос без `CREATE VIEW`, изучите несколько "
            "групп, проверьте уникальность результата, затем сохраните запрос как представление.\n\n"
            "**Частые ошибки:** неверная гранулярность, `DISTINCT` скрывает конфликт, отсутствует "
            "tie-breaker, фильтр `rn = 1` поставлен на неправильном уровне, NULL сравнивается через `=`.\n\n"
            f"<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"
        ),
        code(
            "%%sql\n"
            f"-- CREATE OR REPLACE VIEW training.{view_name} AS\n"
            "-- SELECT ...;\n"
        ),
        code(
            "%%sql\n"
            f"-- Ручная проверка результата:\n-- SELECT * FROM training.{view_name} LIMIT 20;"
        ),
        *([md("<details><summary><strong>Эталонное решение и разбор</strong></summary>\n\n"
             f"```sql\n{SOLUTIONS[number][0]}\n```\n\n**Что делаем:** {SOLUTIONS[number][1]}\n\n"
             "После создания VIEW проверьте число строк и уникальность бизнес-ключа.\n\n</details>")]
          if number in SOLUTIONS else []),
        code(
            "%%sql\n"
            f"SELECT * FROM training.run_checks('deduplication', {number});"
        ),
    ])

cells.extend([
    md("## Прогресс"),
    code(
        "%%sql\n"
        "SELECT task_no, tests_passed, tests_total, completed, checked_at\n"
        "FROM training.progress\n"
        "WHERE module_name = 'deduplication'\n"
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
