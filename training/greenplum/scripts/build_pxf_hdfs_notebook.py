import os
from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parent.parent
OUTPUT=Path(os.environ.get("GREENPLUM_PXF_OUTPUT",ROOT/"notebooks"/"05_PXF_HDFS_Parquet_30_Tasks.ipynb"))
tasks=[
("gpx_01_config","Создайте VIEW параметров PXF/HDFS стенда.","NameNode и server profile уже настроены."),
("gpx_02_metrica_ext","Исследуйте существующую dds external Метрики и создайте metadata VIEW.","Читайте pg_exttable, не пересоздавайте source."),
("gpx_03_metrica_count","Зафиксируйте count и диапазон дат PXF-источника.","Внешний count обращается к HDFS."),
("gpx_04_metrica_profile","Профилируйте страны, города, IP и даты.","Этот профиль понадобится для физической модели."),
("gpx_05_projection","Сравните чтение 4 колонок и SELECT *.","Parquet читает только нужные column chunks."),
("gpx_06_predicate","Сравните фильтр по дате с полным чтением.","Проверьте PXF filter в плане."),
("gpx_07_fragments","Создайте VIEW распределения прочитанных строк по gp_segment_id.","PXF назначает fragments сегментам."),
("gpx_08_file_layout","Создайте VIEW количества HDFS файлов/партиций источника.","Метаданные можно получить через подготовленный manifest."),
("gpx_09_schema_map","Создайте VIEW Greenplum↔Parquet типов Метрики.","Особенно даты, bigint и nullable."),
("gpx_10_null_profile","Профилируйте NULL важных колонок.","Schema совместимость включает nullability."),
("gpx_11_countries_write","Создайте writable PXF Parquet для countries.","Путь только внутри /data/raw/m_razhin."),
("gpx_12_countries_insert","Запишите 173 страны в HDFS и сохраните audit count.","Сначала writable, потом readable."),
("gpx_13_countries_read","Создайте readable PXF над созданными Parquet-файлами.","Используйте файловый wildcard."),
("gpx_14_roundtrip","Сверьте count и checksum countries round-trip.","Порядок строк не гарантирован."),
("gpx_15_append","Добавьте второй batch и покажите append semantics.","Writable PXF не делает overwrite."),
("gpx_16_partition_path","Запишите данные в путь вида load_date=YYYY-MM-DD.","Каталог может кодировать partition value."),
("gpx_17_multi_path","Создайте readable table над несколькими partition paths.","Wildcard должен выбирать ожидаемые файлы."),
("gpx_18_path_column","Добавьте partition value в результат безопасным способом.","Не путайте физическую колонку и имя каталога."),
("gpx_19_small_files","Создайте VIEW оценки small-file problem.","Много маленьких fragments создаёт overhead."),
("gpx_20_compaction","Выполните учебную compaction в новый каталог.","Не перезаписывайте читаемый source на месте."),
("gpx_21_moex_ext","Исследуйте external MOEX Parquet и его LOCATION.","Путь уже партиционирован по SECID/date."),
("gpx_22_moex_filter","Прочитайте один ticker/day и измерьте строки/fragments.","Фильтр должен совпасть с путём и колонками."),
("gpx_23_moex_projection","Сравните узкую и широкую проекцию сделок.","Витрине нужны не все source fields."),
("gpx_24_type_mismatch","Воспроизведите безопасную ошибку несовместимого типа.","Сохраните SQLSTATE и сообщение."),
("gpx_25_missing_path","Диагностируйте отсутствующий HDFS path.","Различайте no files и connection failure."),
("gpx_26_pxf_status","Создайте VIEW статуса PXF обоих segment hosts.","Проверяется порт 5888 на sdw1/sdw2."),
("gpx_27_external_vs_internal","Сравните план/время external и внутренней AO copy.","Частое чтение может оправдать материализацию."),
("gpx_28_pushdown_report","Создайте отчёт predicate/projection pushdown нескольких запросов.","Не каждый SQL-предикат можно передать источнику."),
("gpx_29_reconciliation","Сверьте HDFS manifest, external count и internal target.","Три уровня должны согласоваться."),
("gpx_30_pipeline","Создайте итоговый VIEW PXF pipeline со статусами.","HDFS→PXF external→quality→internal→reconciliation."),
]
def md(x): return nbf.v4.new_markdown_cell(x)
def code(x): return nbf.v4.new_code_cell(x)
cells=[
md("# PXF, HDFS и Parquet — 30 заданий\n\nPXF выполняется рядом с segment hosts и даёт Greenplum параллельный доступ к HDFS. Все writable пути ограничены `/data/raw/m_razhin`; исходные Метрика и MOEX только читаются."),
code("%load_ext sql\n%config SqlMagic.displaylimit = 150\n%sql postgresql+psycopg2://gpadmin@cbdb-coordinator:5432/moex"),
md("## 1. Что такое PXF\n\nPlatform Extension Framework состоит из Greenplum extension и PXF server на segment hosts. External table хранит URI/profile/options. Во время запроса сегменты получают fragments и обращаются к PXF server, который использует Hadoop client."),
md("## 2. Profile\n\nProfile выбирает connector и формат, например `hdfs:parquet`. Он определяет reader/writer и допустимые options. Неверный profile — ошибка конфигурации, а не SQL-типов."),
md("## 3. Fragment\n\nFragment — единица внешней работы: файл, блок или логическая часть источника. PXF распределяет fragments между сегментами. Один файл не всегда равен одному fragment, но большое число маленьких файлов почти всегда создаёт planning/open overhead."),
md("## 4. Parquet\n\nParquet — колоночный self-describing формат с row groups, column chunks, статистикой и compression. PXF сопоставляет физические поля с колонками external table. Порядок/имена и типы зависят от настроек reader и файла."),
md("## 5. Projection pushdown\n\nЕсли SQL выбирает несколько колонок, Parquet reader может не читать остальные chunks. Выигрыш особенно велик на широкой таблице. `SELECT *`, функции над многими колонками и последующая ненужная проекция увеличивают I/O."),
md("## 6. Predicate pushdown\n\nЧасть фильтра передаётся PXF/reader и позволяет пропустить row groups/files. В плане ищите PXF filter. Сложные функции, несовместимые cast и некоторые выражения остаются фильтром Greenplum после чтения."),
md("## 7. Partitioned paths\n\nHDFS-каталоги часто имеют вид `key=value`. Это физическая организация, но не автоматически колонка Greenplum. Hive может добавлять partition column из metastore; прямой PXF path требует явного проектирования."),
md("## 8. Readable external\n\nCREATE не проверяет весь набор и не копирует данные. Ошибки path, schema или type могут проявиться на SELECT. External object не имеет обычной Greenplum distribution policy хранения; распределяется работа чтения."),
md("## 9. Writable external\n\nINSERT создаёт новые файлы. Обычно это append, не overwrite и не транзакционная замена каталога. Не пытайтесь читать ещё не созданный путь до первой записи: некоторые слои кэшируют отрицательный результат."),
md("## 10. Schema evolution\n\nДобавление nullable поля в новые Parquet-файлы может быть совместимо, но смешанный каталог нужно тестировать. Переименование, изменение типа и перестановка при positional mapping опасны. Schema contract хранится вместе с pipeline."),
md("## 11. Типы\n\nParquet INT64 может соответствовать bigint/timestamp в зависимости logical annotation. Decimal требует precision/scale. Date и timestamp нуждаются в проверке timezone semantics. Строка, объявленная bigint, даст runtime conversion error."),
md("## 12. Small files\n\nТысячи маленьких файлов ухудшают list/status/open, увеличивают fragments и нагрузку NameNode. Compaction читает набор и пишет меньше крупных файлов в новый каталог, затем consumer переключается после проверки."),
md("## 13. External или internal\n\nExternal хорош для raw/редкого чтения и обмена. Внутренняя AO column даёт статистику Greenplum, контролируемое distribution, локальные scan и предсказуемые JOIN. Решение зависит от частоты, SLA и стоимости повторного HDFS-чтения."),
md("## 14. Диагностика\n\nРазделяйте уровни: SQL DDL, extension, PXF server 5888, Hadoop config, NameNode/DataNode, path/permissions, file format/schema. `connection refused`, `FileNotFound` и type mismatch требуют разных действий."),
md("## 15. Reconciliation\n\nСравнивайте HDFS manifest (files/bytes), external rows, accepted/rejected и internal rows/checksum. Count без checksum не выявляет подмену значений; checksum без count может скрыть особенности агрегации."),
md("## 16. Порядок работы\n\n1. Проверить PXF status. 2. Проверить HDFS path. 3. Создать readable external. 4. LIMIT/profile. 5. Count/schema quality. 6. Проверить pushdown. 7. При необходимости записать новый каталог. 8. Создать readable readback. 9. Reconcile. 10. Материализовать target."),
]
for n,(obj,prompt,hint) in enumerate(tasks,1):
    if n==11: cells.append(md("## Уровень 2 — writable Parquet и round-trip"))
    if n==21: cells.append(md("## Уровень 3 — MOEX, диагностика и архитектурный выбор"))
    cells += [md(f"### Задание {n}. `m_razhin.{obj}`\n\n**Что сделать:** {prompt}\n\nНе изменяйте исходные HDFS-каталоги. Для writable используйте уникальный подкаталог `training/pxf/...` внутри персонального пути.\n\n<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"),
      code(f"%%sql\nSET search_path TO m_razhin,public;\n-- Создайте m_razhin.{obj} здесь."),
      code("%%sql\n-- Ручная проверка external/readback/manifest."),
      code(f"%%sql\nSELECT * FROM greenplum_training.run_checks('pxf_hdfs',{n});")]
cells += [md("## Прогресс"),code("%%sql\nSELECT * FROM greenplum_training.progress WHERE module_name='pxf_hdfs' ORDER BY task_no;")]
nb=nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3 (ipykernel)","language":"python","name":"python3"}})
OUTPUT.parent.mkdir(parents=True,exist_ok=True); nbf.write(nb,OUTPUT); print(OUTPUT)
