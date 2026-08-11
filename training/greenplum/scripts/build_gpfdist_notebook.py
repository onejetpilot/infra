import os
from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parent.parent
OUTPUT=Path(os.environ.get("GREENPLUM_GPFDIST_OUTPUT",ROOT/"notebooks"/"04_GPFDIST_30_Tasks.ipynb"))
tasks=[
("gpg_01_endpoint","Создайте VIEW с host, port, path и ожидаемым URL учебного GPFDIST.","Источник уже работает на cdw:8080."),
("gpg_02_countries_ext","Создайте readable external table над countries.csv.","Файл без header, разделитель запятая."),
("gpg_03_source_count","Создайте VIEW количества строк внешней таблицы.","Ожидается 173 строки."),
("gpg_04_source_profile","Профилируйте NULL, distinct codes/names и длины.","Внешнюю таблицу сначала исследуют."),
("gpg_05_countries_heap","Загрузите источник во внутреннюю heap-таблицу.","INSERT SELECT из external."),
("gpg_06_countries_ao","Загрузите в AO column zstd.","Для маленькой таблицы выигрыш не обязателен."),
("gpg_07_countries_repl","Создайте replicated-справочник.","Проверяется policy и логический count."),
("gpg_08_trim","Создайте очищенную таблицу с trim строк.","Не скрывайте пустые значения как NULL без правила."),
("gpg_09_constraints","Создайте quality VIEW дублей и некорректных кодов.","External table не заменяет quality checks."),
("gpg_10_reconciliation","Сверьте source и target count/checksum.","Идемпотентность начинается с reconciliation."),
("gpg_11_header_ext","Создайте external table для CSV с HEADER.","HEADER относится к каждому URI-фрагменту."),
("gpg_12_delimiter_ext","Создайте external table с нестандартным delimiter.","Явно задайте FORMAT options."),
("gpg_13_quote_escape","Обработайте delimiter внутри quoted field.","QUOTE и ESCAPE — разные параметры."),
("gpg_14_null_mapping","Настройте представление NULL в CSV.","Пустая строка и NULL семантически различаются."),
("gpg_15_encoding","Зафиксируйте encoding внешней таблицы.","Несовпадение кодировки проявляется при parsing."),
("gpg_16_bad_rows","Создайте внешний источник с контролируемыми ошибками.","Используйте учебный bad CSV."),
("gpg_17_reject_limit","Настройте SEGMENT REJECT LIMIT.","Одна плохая строка не должна отменять допустимую загрузку."),
("gpg_18_error_log","Создайте VIEW диагностики rejected rows.","Сохраните raw line и причину."),
("gpg_19_reject_threshold","Продемонстрируйте превышение reject limit безопасно.","Эксперимент выполняйте на учебном файле."),
("gpg_20_type_conversion","Загрузите typed staging с безопасной конверсией.","Сырые строки и typed слой разделяются."),
("gpg_21_multi_location","Создайте external table с несколькими LOCATION.","Каждый URI должен иметь совместимую схему."),
("gpg_22_parallel_profile","Создайте VIEW строк по gp_segment_id при чтении.","Покажите участие сегментов."),
("gpg_23_distribution_target","Выберите policy внутренней target после GPFDIST.","Внешний источник сам не задаёт policy target."),
("gpg_24_writable_ext","Создайте writable external table для выгрузки CSV.","Writable external table используется через INSERT."),
("gpg_25_export","Выгрузите агрегат в GPFDIST и сохраните count.","Повторная запись может дописать файлы."),
("gpg_26_export_readback","Создайте readable external над экспортом.","Round-trip проверяет формат."),
("gpg_27_roundtrip","Сверьте исходный агрегат и readback checksum.","Count недостаточно для содержимого."),
("gpg_28_idempotent_load","Реализуйте повторяемую загрузку countries без дублей.","Staging + replace/merge pattern."),
("gpg_29_audit","Создайте audit VIEW: source,target,rejected,status.","Статус основан на измерениях."),
("gpg_30_pipeline","Создайте итоговый VIEW всех этапов GPFDIST pipeline.","Endpoint→external→quality→target→reconciliation."),
]
def md(x): return nbf.v4.new_markdown_cell(x)
def code(x): return nbf.v4.new_code_cell(x)
cells=[
md("# GPFDIST — 30 заданий\n\nGPFDIST передаёт файлы сегментам Greenplum по HTTP. Курс использует `gpfdist://cdw:8080`, существующий `countries.csv` и отдельные учебные файлы. Рабочие объекты — только `m_razhin`."),
code("%load_ext sql\n%config SqlMagic.displaylimit = 100\n%sql postgresql+psycopg2://gpadmin@cbdb-coordinator:5432/moex"),
md("## 1. Зачем GPFDIST\n\nОбычный клиентский INSERT пропускает данные через одно соединение coordinator. GPFDIST позволяет segment processes параллельно читать части файла или писать выходные фрагменты. Это транспорт, а не формат хранения и не база данных."),
md("## 2. Архитектура\n\n```text\nfiles → gpfdist HTTP server ← segment processes\n                         ↑\n                 external table metadata\n```\n\nCoordinator хранит определение external table и планирует запрос. Сегменты обращаются к URI. Поэтому имя host должно разрешаться из Docker-сети сегментов, а порт — быть доступен им, не только Windows."),
md("## 3. Readable external table\n\nReadable external table описывает колонки, LOCATION, FORMAT, encoding и error policy. Она не копирует данные при CREATE. Каждый SELECT заново читает источник. Изменение файла меняет результат без DDL."),
md("## 4. CSV parsing\n\nDelimiter разделяет поля вне quotes. QUOTE позволяет включить delimiter/newline в значение. ESCAPE кодирует quote/escape. HEADER пропускает первую строку каждого файла. NULL marker задаёт специальное текстовое представление отсутствующего значения."),
md("## 5. Сначала raw text\n\nНадёжный ingestion часто разделяет raw external с текстовыми колонками и typed staging. Если сразу объявить integer/date, одна некорректная строка становится parsing error до выполнения вашего SELECT."),
md("## 6. Reject handling\n\n`SEGMENT REJECT LIMIT` разрешает пропустить ограниченное число или процент ошибочных строк на сегменте. Это не означает «игнорировать качество»: rejected rows должны учитываться, диагностироваться и иметь согласованный порог остановки."),
md("### Почему limit сегментный\n\nОшибка считается там, где строка обрабатывается. При неравномерном распределении входных фрагментов один сегмент может превысить limit раньше общего ожидаемого числа. Поэтому анализируют и абсолютное количество, и распределение ошибок."),
md("## 7. Внутренняя target\n\nExternal table подходит для ingress, но регулярные JOIN обычно выполняют по внутренней AO/heap target с выбранной distribution policy, статистикой и quality constraints. Этапы: external raw → profile → typed staging → target → reconciliation."),
md("## 8. Несколько LOCATION\n\nНесколько URI увеличивают параллелизм и позволяют читать файловые shards. Все фрагменты обязаны иметь совместимые формат и схему. HEADER будет применён к каждому URI, что правильно только если каждый shard имеет собственный header."),
md("## 9. Writable external\n\nINSERT в writable external отправляет строки GPFDIST, который создаёт выходные файлы/фрагменты. Повторный INSERT не является автоматическим overwrite. Идемпотентность экспорта требует управления каталогом и именем выгрузки."),
md("## 10. Производительность\n\nНа скорость влияют число и размер файлов, ширина строк, parsing, сеть, число сегментов и последующая target policy. Много крошечных файлов создаёт overhead; один огромный источник может ограничить параллелизм."),
md("## 11. Диагностика\n\nПроверяйте процесс/порт GPFDIST, DNS host из сегмента, LOCATION, права на каталог, логи сервера, FORMAT и encoding. Ошибка `connection refused` отличается от parse error: первая до чтения данных, вторая после получения bytes."),
md("## 12. Безопасность\n\nGPFDIST предоставляет файлы из заданного server directory. Не запускайте его от root и не публикуйте каталог с секретами. В учебном стенде endpoint доступен внутри Docker-сети; это не production security model."),
md("## 13. Идемпотентная загрузка\n\nПовтор запуска должен давать тот же target. Для маленького справочника допустим transaction + truncate/insert. Для больших периодов — staging, проверки и exchange/delete+insert по slice. Всегда сохраняйте audit counts."),
md("## 14. Reconciliation\n\nМинимум сравнивают source count, accepted count, rejected count и target count. Для содержимого используют агрегированный checksum по каноническому представлению колонок. Суммы/минимумы полезны, но не доказывают полное равенство."),
md("## 15. Порядок практики\n\n1. Проверить endpoint. 2. Создать raw external. 3. Посмотреть строки и профиль. 4. Настроить error policy. 5. Загрузить staging. 6. Выполнить quality checks. 7. Загрузить target. 8. ANALYZE. 9. Reconcile. 10. Проверить повторный запуск."),
]
for n,(obj,prompt,hint) in enumerate(tasks,1):
    if n==11: cells.append(md("## Уровень 2 — CSV и rejected rows"))
    if n==21: cells.append(md("## Уровень 3 — parallel locations, export и pipeline"))
    cells += [md(f"### Задание {n}. `m_razhin.{obj}`\n\n**Что сделать:** {prompt}\n\nПеред DDL запишите ожидаемый формат и failure mode. После — проверьте count, quality и системный каталог.\n\n<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"),
      code(f"%%sql\nSET search_path TO m_razhin,public;\n-- Создайте m_razhin.{obj} здесь."),
      code("%%sql\n-- Ручная проверка external/target/audit."),
      code(f"%%sql\nSELECT * FROM greenplum_training.run_checks('gpfdist',{n});")]
cells += [md("## Прогресс"),code("%%sql\nSELECT * FROM greenplum_training.progress WHERE module_name='gpfdist' ORDER BY task_no;")]
nb=nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3 (ipykernel)","language":"python","name":"python3"}})
OUTPUT.parent.mkdir(parents=True,exist_ok=True); nbf.write(nb,OUTPUT); print(OUTPUT)
