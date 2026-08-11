import os
from pathlib import Path
import nbformat as nbf

ROOT=Path(__file__).resolve().parent.parent
OUTPUT=Path(os.environ.get("GREENPLUM_STORAGE_OUTPUT",ROOT/"notebooks"/"02_Storage_Partitioning_30_Tasks.ipynb"))

tasks=[
("gps_01_heap","Создайте heap-копию `storage_source`, распределённую по event_id.","Heap задаётся отсутствием appendoptimized=true."),
("gps_02_ao_row","Создайте append-optimized row table без сжатия.","WITH (appendoptimized=true, orientation=row)."),
("gps_03_ao_column","Создайте append-optimized column table без сжатия.","orientation=column."),
("gps_04_ao_zlib","Создайте AO column с zlib и уровнем 5.","compresstype=zlib, compresslevel=5."),
("gps_05_ao_zstd","Создайте AO column с zstd и уровнем 5.","Проверьте поддержку алгоритма данным кластером."),
("gps_06_ao_rle","Создайте AO column с RLE_TYPE для подходящих колонок.","RLE особенно полезен повторяющимся значениям."),
("gps_07_storage_catalog","Создайте VIEW параметров хранения таблиц 01–06.","Используйте pg_appendonly и pg_class."),
("gps_08_table_sizes","Создайте VIEW total/heap/index/ao размера каждого варианта.","Сравнивайте одинаковое число строк."),
("gps_09_compression_ratio","Создайте VIEW коэффициента размера относительно heap.","ratio = heap_size / variant_size."),
("gps_10_scan_benchmark","Создайте таблицу результатов времени/плана чтения нескольких колонок.","Не делайте вывод по единственному случайному запуску."),
("gps_11_range_partition","Создайте range-partitioned таблицу по event_date с месячными партициями.","Исходник содержит 90 дней."),
("gps_12_partition_catalog","Создайте VIEW дерева партиций, границ и физических имён.","Используйте системные представления partition metadata."),
("gps_13_partition_counts","Создайте VIEW количества строк в каждой leaf partition.","Считать нужно физические leaf-таблицы."),
("gps_14_pruning_plan","Сохраните число просканированных partitions для фильтра одного месяца.","Проверяйте EXPLAIN."),
("gps_15_no_pruning","Покажите число partitions при выражении, мешающем pruning.","Сравните с sargable-предикатом."),
("gps_16_default_partition","Создайте таблицу с default partition и загрузите строку вне диапазона.","Default принимает данные без подходящей явной части."),
("gps_17_add_partition","Добавьте новую месячную partition и загрузите строки этого месяца.","Границы не должны пересекаться."),
("gps_18_drop_partition","На учебной копии удалите старую partition и подтвердите изменение дерева.","DROP PARTITION удаляет данные части."),
("gps_19_truncate_partition","Очистите одну partition без изменения остальных.","TRUNCATE PARTITION быстрее DELETE всех строк."),
("gps_20_split_default","Перенесите диапазон из default в явную partition.","Используйте SPLIT DEFAULT PARTITION."),
("gps_21_staging_like","Создайте staging через LIKE целевой leaf-структуры.","Типы и physical options должны быть совместимы."),
("gps_22_stage_latest","Загрузите в staging данные последней даты источника.","До exchange проверьте только нужный диапазон."),
("gps_23_change_key","Измените event_date staging на следующий месяц.","Все строки должны попасть в границы новой partition."),
("gps_24_add_exchange_target","Добавьте пустую target partition для нового месяца.","Сначала DDL, затем exchange."),
("gps_25_exchange_without_validation","Выполните Direct Partition Exchange со staging.","WITHOUT VALIDATION допустим только после своей проверки."),
("gps_26_exchange_counts","Создайте VIEW сверки строк до/после exchange.","Проверяйте target и бывшую leaf-таблицу."),
("gps_27_exchange_metadata","Докажите, что exchange меняет metadata, а не переписывает строки.","Сравните relfilenode/размер до и после."),
("gps_28_multilevel","Создайте двухуровневую таблицу: месяц → list(country).","Не создавайте чрезмерное число мелких leaf partitions."),
("gps_29_partition_skew","Создайте VIEW skew по каждой leaf partition.","Объедините partition tree и gp_segment_id counts."),
("gps_30_recommendation","Создайте итоговый VIEW: объект, storage, compression, size, pruning, skew, verdict.","Рекомендация должна опираться на измерения."),
]
def md(x): return nbf.v4.new_markdown_cell(x)
def code(x): return nbf.v4.new_code_cell(x)

cells=[
md("# Хранение, сжатие и партиционирование — 30 заданий\n\nМодуль сравнивает физические варианты на одинаковых данных. Все объекты создаются в `m_razhin`; источник `greenplum_training.storage_source` восстанавливается и не используется другими проектами."),
code("%load_ext sql\n%config SqlMagic.displaylimit = 100\n%sql postgresql+psycopg2://gpadmin@cbdb-coordinator:5432/moex"),
md("## 1. Логическая и физическая модель\n\nDDL определяет не только колонки. Для Greenplum важны четыре независимых решения: distribution policy, способ хранения, compression и partitioning. Один хороший параметр не компенсирует другой: сжатая таблица всё равно может иметь skew, а идеально распределённая — читать лишние партиции."),
md("## 2. Heap\n\nHeap наследует модель PostgreSQL: строки размещаются построчно, UPDATE/DELETE естественно создают новые версии MVCC, возможны индексы. Heap удобен для небольших изменяемых таблиц и справочников. Для большого append-only факта он часто уступает AO по последовательной загрузке, сжатию и аналитическому чтению."),
md("### MVCC и обслуживание heap\n\nUPDATE фактически создаёт новую версию, DELETE помечает старую невидимой. Старые версии занимают место до vacuum. Массовый ежедневный факт обычно лучше загружать новыми порциями, чем постоянно обновлять каждую строку."),
md("## 3. Append-optimized row\n\nAO row хранит последовательности добавленных строк и оптимизирован для bulk load и scan. Он не означает, что SQL-команда `UPDATE` синтаксически невозможна, но частые мелкие изменения противоречат назначению. AO row полезен, когда запрос обычно читает большую часть колонок."),
md("## 4. Append-optimized column\n\nAO column хранит колонки раздельно по row groups. Запрос, выбирающий пять колонок из пятидесяти, читает меньше данных. Однотипные значения лучше сжимаются. Цена — невыгодное точечное чтение всей строки и сложность частых изменений."),
md("### Проекция колонок\n\nКолоночное хранение помогает только если запрос действительно выбирает часть колонок. `SELECT *` заставляет прочитать все column streams. При проектировании витрины учитывайте реальные SELECT-листы аналитиков."),
md("## 5. Compression\n\nСжатие уменьшает I/O и иногда ускоряет запрос, хотя требует CPU. `zlib` обычно сжимает сильнее, `zstd` даёт хороший баланс скорости и размера, RLE_TYPE эффективно кодирует длинные серии одинаковых значений. Результат зависит от порядка строк, типов и данных — алгоритм выбирают измерением."),
md("### Compress level\n\nБолее высокий уровень не гарантирует лучший end-to-end результат. Дополнительный CPU может превышать экономию чтения. Сравнивайте размер, время загрузки и несколько типовых запросов после прогрева."),
md("## 6. Измерение размера\n\n`pg_relation_size` показывает основной физический объект, `pg_total_relation_size` включает дополнительные структуры. У partitioned parent почти нет пользовательских строк: размер нужно суммировать по leaf partitions. В Greenplum размер следует понимать как сумму файлов всех сегментов."),
md("## 7. Partitioning\n\nPartitioning делит одну логическую таблицу на физические leaf-таблицы по правилу. Основная польза — partition pruning и управление жизненным циклом: быстро добавить, обменять, очистить или удалить период."),
md("### Range, list и default\n\nRange подходит датам и числовым интервалам; обычно используется полуинтервал `[start,end)`. List подходит небольшому фиксированному набору категорий. Default принимает всё, что не соответствует явным частям, но может скрывать ошибку маршрутизации."),
md("### Сколько партиций\n\nСлишком крупная partition читает лишние данные и неудобна для обслуживания. Слишком мелкие части увеличивают каталоги, время планирования и число файлов. Гранулярность выбирают по фильтрам, объёму периода и операциям загрузки/удаления."),
md("## 8. Partition pruning\n\nOptimizer исключает leaf partitions, границы которых несовместимы с предикатом. Наиболее надёжен прямой sargable-фильтр по partition key. Функция, cast или сложное выражение над ключом может ограничить статический pruning."),
code("%%sql\nEXPLAIN SELECT count(*)\nFROM m_razhin.gps_11_range_partition\nWHERE event_date>=DATE '2025-02-01' AND event_date<DATE '2025-03-01';"),
md("## 9. Direct Partition Exchange\n\nExchange меняет привязку физической таблицы к partition metadata. Это позволяет почти мгновенно заменить большой период: данные заранее готовятся и проверяются в staging, затем staging и leaf меняются местами без обычной перезаписи всех строк."),
md("### Совместимость staging\n\nКолонки, типы, порядок, distribution policy и storage options должны быть совместимы. `LIKE` уменьшает риск расхождения, но не заменяет проверку диапазона данных. Staging не должна содержать строки вне target boundaries."),
md("### WITH/WITHOUT VALIDATION\n\nС validation СУБД проверяет границы, что безопаснее, но может просканировать staging. `WITHOUT VALIDATION` быстрее и переносит ответственность на ETL. Перед ним обязательны собственные count, min/max key, NULL и quality checks."),
md("### Безопасная последовательность exchange\n\n1. Создать совместимую staging. 2. Загрузить данные. 3. Выполнить quality checks. 4. Добавить target partition. 5. Exchange. 6. Проверить counts и границы через parent. 7. Решить судьбу бывшей partition, оказавшейся staging-таблицей."),
md("## 10. Типичные ошибки\n\n- сравнивать размеры таблиц с разным числом строк;\n- считать только parent partitioned table;\n- выбирать compression по одному запросу;\n- путать distribution key и partition key;\n- использовать `SELECT *` и ждать выигрыша column orientation;\n- выполнять exchange до проверки диапазона;\n- создавать тысячи крошечных partitions."),
md("## 11. Порядок практики\n\nСначала создавайте варианты на одном источнике, проверяйте count и policy, выполняйте ANALYZE, затем измеряйте размер и план. Для partition DDL всегда проверяйте дерево до и после операции. Не выполняйте опасные команды на `dds` или рабочей таблице задания."),
]
for n,(obj,prompt,hint) in enumerate(tasks,1):
    if n==11: cells.append(md("## Уровень 2 — partitioning и pruning"))
    if n==21: cells.append(md("## Уровень 3 — Direct Partition Exchange"))
    cells += [
      md(f"### Задание {n}. `m_razhin.{obj}`\n\n**Что сделать:** {prompt}\n\nДо выполнения запишите ожидаемый storage/partition effect. После — проверьте системный каталог, count и физический размер или план.\n\n<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"),
      code(f"%%sql\nSET search_path TO m_razhin,public;\n-- Создайте или измените m_razhin.{obj} здесь."),
      code(f"%%sql\n-- Ручная проверка объекта, каталога, count или EXPLAIN."),
      code(f"%%sql\nSELECT * FROM greenplum_training.run_checks('storage_partitioning',{n});")
    ]
cells += [md("## Прогресс"),code("%%sql\nSELECT * FROM greenplum_training.progress WHERE module_name='storage_partitioning' ORDER BY task_no;")]
nb=nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3 (ipykernel)","language":"python","name":"python3"}})
OUTPUT.parent.mkdir(parents=True,exist_ok=True); nbf.write(nb,OUTPUT); print(OUTPUT)
