import os
from pathlib import Path

import nbformat as nbf
from window_solutions import SOLUTIONS

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = Path(os.environ.get(
    "SQL_COURSE_OUTPUT",
    ROOT / "notebooks" / "03_Window_Functions_30_Tasks.ipynb",
))

tasks = [
    ("wf_01", "Пронумеруйте заказы по времени покупки; верните order_id, purchased_at, row_num.", "row_number() over(order by ...)"),
    ("wf_02", "Пронумеруйте заказы отдельно для каждого статуса.", "partition by order_status"),
    ("wf_03", "Постройте ранг заказов по payment_value без пропусков рангов.", "dense_rank"),
    ("wf_04", "Сравните row_number, rank и dense_rank на платежах.", "Одинаковые значения образуют ничью."),
    ("wf_05", "Верните три самых дорогих заказа каждого штата.", "Окно в CTE, фильтр снаружи."),
    ("wf_06", "Найдите первый заказ каждого customer_unique_id.", "row_number по покупателю."),
    ("wf_07", "Найдите последний заказ каждого покупателя.", "DESC и детерминированный tie-breaker."),
    ("wf_08", "Добавьте к заказу предыдущую дату покупки клиента.", "lag"),
    ("wf_09", "Посчитайте дни между соседними заказами клиента.", "Текущая дата минус lag."),
    ("wf_10", "Добавьте следующую покупку клиента.", "lead"),
    ("wf_11", "Посчитайте накопительную выручку по дням.", "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW"),
    ("wf_12", "Посчитайте накопительную выручку отдельно по году.", "partition by extract(year...)."),
    ("wf_13", "Рассчитайте скользящее среднее выручки за 7 строк-дней.", "ROWS 6 PRECEDING."),
    ("wf_14", "Рассчитайте календарное среднее за текущий и шесть предыдущих дней.", "RANGE с interval после заполнения дат."),
    ("wf_15", "Добавьте общую выручку категории к каждой строке товара.", "sum(...) over(partition by category)."),
    ("wf_16", "Рассчитайте долю товара в выручке категории.", "Деление на оконную сумму и NULLIF."),
    ("wf_17", "Сравните выручку месяца с предыдущим месяцем.", "lag по агрегированным месяцам."),
    ("wf_18", "Рассчитайте абсолютное и процентное изменение месяца.", "CTE, lag один раз."),
    ("wf_19", "Найдите максимальную выручку на текущий момент.", "max с накопительным frame."),
    ("wf_20", "Верните первое и последнее значение месяца в году.", "Для last_value нужен frame до UNBOUNDED FOLLOWING."),
    ("wf_21", "Разбейте покупателей на четыре группы по LTV.", "ntile(4)."),
    ("wf_22", "Рассчитайте percent_rank покупателей по LTV.", "percent_rank."),
    ("wf_23", "Рассчитайте cume_dist товаров по выручке.", "cume_dist."),
    ("wf_24", "Найдите медиану платежа по типу платежа.", "percentile_cont как ordered-set aggregate."),
    ("wf_25", "Найдите серии последовательных календарных дней с заказами.", "Gaps and islands через date - row_number."),
    ("wf_26", "Сформируйте пользовательские сессии: новый сеанс после перерыва более 30 дней.", "lag, флаг границы, накопительная sum."),
    ("wf_27", "Найдите повторные покупки в течение 30 дней после первой.", "first_value или min over partition."),
    ("wf_28", "Постройте cohort month и номер месяца жизни заказа.", "min(purchased_at) over partition."),
    ("wf_29", "Рассчитайте retention по когорте и month_number.", "Сначала уникальные клиент-месяцы."),
    ("wf_30", "Соберите ABC-классификацию товаров по накопительной доле выручки.", "Сумма, running share, CASE A/B/C."),
]

def md(x): return nbf.v4.new_markdown_cell(x)
def code(x): return nbf.v4.new_code_cell(x)

cells = [
    md("# Оконные функции PostgreSQL — 30 заданий\n\nОконная функция считает показатель по связанным строкам, но не схлопывает их как `GROUP BY`. Решения сохраняются как представления `training.wf_01`–`training.wf_30`."),
    code("%load_ext sql\n%config SqlMagic.displaylimit = 50\n%sql postgresql+psycopg2://student:sqltrain2026@sql-train-db:5432/sql_train"),
    md("## 1. Ментальная модель окна\n\n```sql\nfunction(value) OVER (PARTITION BY group_key ORDER BY sort_key ROWS ...)\n```\n\n`PARTITION BY` делит строки на независимые группы, `ORDER BY` задаёт последовательность внутри группы, frame выбирает часть этой последовательности относительно текущей строки. Результат возвращается для каждой исходной строки."),
    md("## 2. Окна и GROUP BY\n\n`GROUP BY` превращает много строк в одну строку группы. Окно вычисляется после формирования строк результата и сохраняет их количество. Поэтому оконную функцию нельзя фильтровать в `WHERE` того же уровня: вычислите её в CTE/подзапросе, затем фильтруйте снаружи."),
    code("%%sql\nWITH demo(customer, amount) AS (VALUES ('A',10),('A',20),('B',5))\nSELECT customer, amount,\n       sum(amount) OVER (PARTITION BY customer) AS customer_total,\n       row_number() OVER (PARTITION BY customer ORDER BY amount) AS rn\nFROM demo;"),
    md("## 3. Ранжирование\n\n`row_number` всегда выдаёт уникальные номера. `rank` оставляет пропуски после ничьей. `dense_rank` пропусков не оставляет. Если нужна ровно одна строка, сортировка обязана иметь tie-breaker."),
    md("## 4. Смещения\n\n`lag` читает предыдущую строку, `lead` — следующую. Они не ищут «предыдущий день» сами: результат полностью зависит от `ORDER BY`. Для первой/последней строки сосед отсутствует и возвращается NULL."),
    md("## 5. Frame: ROWS и RANGE\n\n`ROWS 6 PRECEDING` означает шесть физических предыдущих строк. Это не семь календарных дней, если даты пропущены. `RANGE` работает по значениям ключа сортировки. Frame по умолчанию часто заканчивается текущей группой равных значений, поэтому `last_value` без явного `UNBOUNDED FOLLOWING` нередко возвращает неожиданное значение."),
    md("## 6. Порядок решения\n\n1. Определите гранулярность строки результата. 2. Назовите partition. 3. Назовите порядок и tie-breaker. 4. Решите, нужен ли frame. 5. Проверьте первую строку, ничью и пропуск даты. 6. Создайте представление и запустите тест."),
]

for n, (view, prompt, hint) in enumerate(tasks, 1):
    if n == 11: cells.append(md("## Уровень 2 — frames и временные ряды"))
    if n == 21: cells.append(md("## Уровень 3 — распределения, сессии и когорты"))
    cells += [
        md(f"### Задание {n}. `training.{view}`\n\n**Результат:** {prompt}\n\nСначала проверьте обычный SELECT. Укажите гранулярность, partition, порядок и frame. Затем создайте представление.\n\n<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"),
        code(f"%%sql\n-- CREATE OR REPLACE VIEW training.{view} AS\n-- SELECT ...;"),
        code(f"%%sql\n-- SELECT * FROM training.{view} LIMIT 20;"),
        *([md("<details><summary><strong>Эталонное решение и разбор</strong></summary>\n\n"
             f"```sql\n{SOLUTIONS[n][0]}\n```\n\n**Что делаем:** {SOLUTIONS[n][1]}\n\n"
             "Проверьте grain, уникальность ключа и граничные строки окна.\n\n</details>")]
          if n in SOLUTIONS else []),
        code(f"%%sql\nSELECT * FROM training.run_checks('window_functions', {n});"),
    ]

cells += [md("## Прогресс"), code("%%sql\nSELECT * FROM training.progress WHERE module_name='window_functions' ORDER BY task_no;")]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec":{"display_name":"Python 3 (ipykernel)","language":"python","name":"python3"}})
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, OUTPUT)
print(OUTPUT)
