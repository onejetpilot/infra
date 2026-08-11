import os
from pathlib import Path
import nbformat as nbf

ROOT=Path(__file__).resolve().parent.parent
OUTPUT=Path(os.environ.get("GREENPLUM_OPTIMIZATION_OUTPUT",ROOT/"notebooks"/"03_Query_Plans_Optimization_30_Tasks.ipynb"))
tasks=[
("gpo_01_explain","Сохраните текст EXPLAIN простого фильтра и выделите scan node.","Используйте учебную функцию explain_lines."),
("gpo_02_analyze","Сравните estimated_rows и actual_rows фильтра.","EXPLAIN ANALYZE действительно выполняет запрос."),
("gpo_03_error_ratio","Рассчитайте cardinality_error_ratio.","max(est/actual,actual/est)."),
("gpo_04_no_stats","Создайте копию без ANALYZE и сохраните ошибку оценки.","Не запускайте ANALYZE автоматически."),
("gpo_05_with_stats","Выполните ANALYZE копии и повторите измерение.","Сравнивайте тот же предикат."),
("gpo_06_column_stats","Создайте VIEW статистики country/hot_key из pg_stats.","Покажите n_distinct, null_frac, most_common_vals/freqs."),
("gpo_07_stats_target","Повышайте statistics target hot_key и повторите ANALYZE.","Проверьте размер MCV списка."),
("gpo_08_seq_scan","Объясните и зафиксируйте scan большого диапазона.","Для аналитики seq scan часто оптимален."),
("gpo_09_projection","Сравните план/байты SELECT двух колонок и SELECT *.","Особенно важно для AO column."),
("gpo_10_filter_pushdown","Покажите, где применяется фильтр относительно Motion.","Фильтр должен сокращать набор до сети."),
("gpo_11_hash_join","Получите Hash Join двух наборов и сохраните показатели.","Равенство и достаточная память благоприятны hash join."),
("gpo_12_nested_loop","Создайте небольшой сценарий Nested Loop и объясните его уместность.","Малый внешний набор — нормальный случай."),
("gpo_13_bad_nested_loop","Воспроизведите дорогой Nested Loop и перепишите запрос.","Смотрите rows loops."),
("gpo_14_broadcast","Измерьте Broadcast Motion маленького измерения.","Сравните размер передаваемого набора."),
("gpo_15_redistribute","Измерьте Redistribute Motion несовместимого JOIN.","Зафиксируйте ключ redistribution."),
("gpo_16_colocated","Перестройте физическую копию для colocated JOIN.","Сравните Motion и total time."),
("gpo_17_join_order","Сравните два порядка JOIN трёх таблиц.","Optimizer может переставлять inner joins."),
("gpo_18_semi_join","Сравните EXISTS и JOIN+DISTINCT.","Semi join не размножает строки."),
("gpo_19_anti_join","Реализуйте anti join через NOT EXISTS и изучите план.","Остерегайтесь NOT IN с NULL."),
("gpo_20_skew_join","Измерьте разброс actual rows/времени сегментов skewed join.","Один content может определять всё время."),
("gpo_21_two_stage_agg","Найдите local и final aggregation stages.","Частичная агрегация уменьшает Motion."),
("gpo_22_group_key","Сравните GROUP BY distribution key и чужой key.","Смотрите Motion между стадиями."),
("gpo_23_distinct","Изучите план count(distinct user_id).","Distinct часто требует перераспределения."),
("gpo_24_sort","Создайте сортировку большого набора и зафиксируйте memory/disk.","ORDER BY без LIMIT требует global order."),
("gpo_25_top_n","Перепишите сортировку для top-N и сравните план.","Top-N heap может уменьшить память."),
("gpo_26_spill","Воспроизведите spill при малой statement memory.","Меняйте параметры только локально."),
("gpo_27_no_spill","Устраните spill изменением запроса или памяти.","Большая память — не единственное решение."),
("gpo_28_partition_plan","Сравните план с pruning и без него.","Считайте реально просканированные leaf."),
("gpo_29_metrica_query","Оптимизируйте типовой запрос Метрики по четырём предикатам.","Измерьте pruning, Motion, rows и время."),
("gpo_30_report","Создайте итоговый VIEW before/after: rows error, motion, spill, time, verdict.","Все выводы должны иметь измерение."),
]
def md(x): return nbf.v4.new_markdown_cell(x)
def code(x): return nbf.v4.new_code_cell(x)
cells=[
md("# Планы выполнения и оптимизация Greenplum — 30 заданий\n\nОптимизация начинается не с переписывания SQL, а с измерения. В модуле используются `greenplum_training.opt_*` и учебные копии `m_razhin`; `EXPLAIN ANALYZE` не запускается на опасных DML."),
code("%load_ext sql\n%config SqlMagic.displaylimit = 200\n%sql postgresql+psycopg2://gpadmin@cbdb-coordinator:5432/moex"),
md("## 1. Что делает optimizer\n\nOptimizer получает логическое дерево запроса и выбирает физический план: порядок JOIN, методы scan/join/aggregate, места Motion и параллельные slices. Он не знает будущее — решения основаны на статистике и cost model."),
md("## 2. Cost не равен миллисекундам\n\n`cost=startup..total` — условные единицы для сравнения вариантов внутри optimizer. Они учитывают оценки CPU, I/O и сети, но не являются прогнозом времени. Сравнивайте cost между планами одного окружения, а реальность — через actual time."),
md("## 3. Estimated и actual rows\n\nОшибка кардинальности распространяется вверх по дереву. Если после фильтра ожидается 10 строк, а приходит миллион, optimizer может выбрать Nested Loop, неверный join order или broadcast. Удобная симметричная метрика — `max(est/actual, actual/est)`."),
md("## 4. EXPLAIN и EXPLAIN ANALYZE\n\n`EXPLAIN` только планирует. `EXPLAIN ANALYZE` выполняет запрос и добавляет actual rows/time/loops. Для INSERT/UPDATE/DELETE это означает реальное изменение; безопасно анализировать DML внутри `BEGIN ... ROLLBACK` либо на учебной копии."),
md("### Как читать план\n\nЧитайте снизу вверх и для каждого узла отвечайте: сколько строк вошло, сколько вышло, где фильтр, сколько loops, есть ли Motion, совпала ли оценка, какой узел определяет critical path. В MPP дополнительно смотрите различия между сегментами."),
md("## 5. Scan\n\nSequential Scan читает доступные блоки и нормален для большой доли аналитической таблицы. Index Scan полезен для селективного точечного доступа, но индекс не отменяет Motion и skew. Для AO column важна column projection."),
md("## 6. Hash Join\n\nBuild side превращается в hash table, probe side ищет совпадения. Метод хорош для equality join. Если строки не colocated, до join появляется Redistribute/Broadcast. Недооценка build side может привести к памяти и spill."),
md("## 7. Nested Loop\n\nДля каждой строки внешнего набора выполняется внутренний доступ. Это отлично при нескольких внешних строках и дешёвом lookup, но катастрофично при большой ошибке cardinality. Всегда умножайте actual rows на loops."),
md("## 8. Join order\n\nInner joins обычно можно переставлять, outer joins ограничивают свободу. Выгодно рано уменьшить набор селективным фильтром, но только если optimizer правильно оценил селективность. CTE и подзапрос не обязаны фиксировать порядок выполнения."),
md("## 9. Semi и anti join\n\n`EXISTS` спрашивает только о наличии и не размножает левую строку. `NOT EXISTS` корректно выражает отсутствие. `NOT IN` при NULL может дать UNKNOWN для всех строк — это семантика, не только производительность."),
md("## 10. Motion как часть плана\n\nRedistribute меняет хеш-размещение, Broadcast копирует набор, Gather собирает. Оценивайте не число надписей Motion, а объём и ширину строк. Один Motion после сильной агрегации может быть дешевле отсутствия ранней агрегации."),
md("## 11. Двухфазная агрегация\n\nСегменты сначала считают partial aggregates локально, затем пересылают компактные состояния и выполняют final aggregate. Эффект максимален, если число групп намного меньше числа исходных строк."),
md("## 12. Sort и top-N\n\nГлобальный ORDER BY требует согласовать порядок между сегментами. Полная сортировка хранит/проливает весь набор. `ORDER BY ... LIMIT N` может использовать локальный top-N на сегментах и объединить небольшие кандидаты."),
md("## 13. Memory и spill\n\nHash, aggregate и sort получают память согласно resource management и statement memory. При нехватке данные пишутся во временные файлы. Spill не всегда ошибка, но большой spill часто означает неверную оценку, слишком широкий набор или отсутствие раннего сокращения."),
md("## 14. Статистика\n\n`ANALYZE` собирает n_distinct, null fraction, most common values, histogram и другие данные. Statistics target управляет детализацией. После крупной загрузки статистику обновляют; чрезмерный target увеличивает время ANALYZE и каталог."),
md("## 15. Коррелированные колонки\n\nОбычная статистика по одной колонке не понимает зависимости вроде country→city. Комбинация предикатов может оцениваться как независимая и давать большую ошибку. Решение зависит от возможностей версии: расширенная статистика, физическая модель или переписывание."),
md("## 16. Partition pruning\n\nPruning уменьшает число scan nodes/leaf. Это не замена фильтру и не distribution. Выражение над partition key, несовместимый тип или неизвестное во время планирования значение могут ограничить pruning."),
md("## 17. Метод оптимизации\n\n1. Зафиксировать SQL и параметры. 2. Получить plan/actual. 3. Найти крупнейшую ошибку rows. 4. Найти большой Motion/spill/skew. 5. Исправить одну причину. 6. ANALYZE при необходимости. 7. Повторить тем же способом. 8. Проверить корректность результата."),
md("## 18. Анти-паттерны\n\nНе отключайте planner methods как постоянное лечение. Не сравнивайте запросы с разным кэшем единственным запуском. Не увеличивайте память без границ. Не убирайте Motion ценой сильного storage skew. Не применяйте `EXPLAIN ANALYZE` к изменяющему production SQL без rollback."),
]
for n,(obj,prompt,hint) in enumerate(tasks,1):
    if n==11: cells.append(md("## Уровень 2 — JOIN и Motion"))
    if n==21: cells.append(md("## Уровень 3 — aggregation, sort, spill и итоговая оптимизация"))
    cells += [
      md(f"### Задание {n}. `m_razhin.{obj}`\n\n**Что сделать:** {prompt}\n\nСохраните измеримые признаки плана в объекте с указанным именем. До изменения сформулируйте гипотезу, после — сравните тем же запросом и подтвердите равенство результата.\n\n<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"),
      code(f"%%sql\nSET search_path TO m_razhin,public;\n-- Создайте m_razhin.{obj} или выполните требуемый эксперимент."),
      code("%%sql\n-- Ручная проверка результата и EXPLAIN/EXPLAIN ANALYZE."),
      code(f"%%sql\nSELECT * FROM greenplum_training.run_checks('query_optimization',{n});")
    ]
cells += [md("## Прогресс"),code("%%sql\nSELECT * FROM greenplum_training.progress WHERE module_name='query_optimization' ORDER BY task_no;")]
nb=nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3 (ipykernel)","language":"python","name":"python3"}})
OUTPUT.parent.mkdir(parents=True,exist_ok=True); nbf.write(nb,OUTPUT); print(OUTPUT)
