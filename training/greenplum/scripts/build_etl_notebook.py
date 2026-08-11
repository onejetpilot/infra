import os
from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parent.parent
OUTPUT=Path(os.environ.get("GREENPLUM_ETL_OUTPUT",ROOT/"notebooks"/"06_ETL_30_Tasks.ipynb"))
tasks=[
("gpe_01_layers","Создайте VIEW-карту raw→staging→dds→dm с гранулярностью.","Слой определяется ответственностью, не только схемой."),
("gpe_02_batch_control","Создайте таблицу batch_control со статусами и timestamps.","Одна строка на попытку загрузки."),
("gpe_03_start_batch","Реализуйте начало batch и сохраните audit.","Статус RUNNING до изменения target."),
("gpe_04_raw_snapshot","Загрузите неизменяемый raw snapshot источника.","Добавьте batch_id и load_dttm."),
("gpe_05_raw_reconcile","Сверьте source/raw count и checksum.","Raw не должен незаметно менять значения."),
("gpe_06_staging_cast","Создайте typed staging с нормализацией.","Ошибочные строки отделяйте."),
("gpe_07_quality_rules","Создайте каталог quality rules и результаты.","Правило имеет severity."),
("gpe_08_rejects","Сохраните rejected records с reason и batch_id.","Не теряйте исходный ключ."),
("gpe_09_full_refresh","Реализуйте атомарный full refresh учебной target.","Пользователь не должен видеть пустое промежуточное состояние."),
("gpe_10_full_idempotent","Докажите одинаковый результат двух full refresh.","Сравните count/checksum."),
("gpe_11_watermark","Создайте watermark по event_date,event_id.","Составная позиция устраняет ничью timestamp."),
("gpe_12_increment","Выберите строки строго после watermark.","Сравнивайте tuple или эквивалентный предикат."),
("gpe_13_increment_load","Загрузите increment в target без дублей.","Уникальность контролируется явно."),
("gpe_14_advance_watermark","Продвиньте watermark только после успешной target.","Ошибка не должна пропустить данные."),
("gpe_15_rerun_increment","Повторите batch и докажите отсутствие дублей.","Exactly-once effect строится поверх повторяемого процесса."),
("gpe_16_late_arrival","Обработайте late event старше watermark.","Нужен overlap window или отдельный канал."),
("gpe_17_upsert_pattern","Реализуйте обновление изменившейся строки.","Greenplum-паттерн staging + delete/insert."),
("gpe_18_changed_rows","Определите changed rows через hashdiff.","Канонизируйте NULL и типы."),
("gpe_19_delete_insert","Перезагрузите один event_date через delete+insert.","Ограничьте транзакцию slice."),
("gpe_20_partition_reload","Перезагрузите месяц через staging/exchange.","Сначала проверка диапазона."),
("gpe_21_deduplicate","Оставьте последнюю версию event_id.","Детерминированный tie-breaker."),
("gpe_22_delete_events","Обработайте tombstone/delete feed.","Физическое или логическое удаление — явная стратегия."),
("gpe_23_scd1","Обновите учебное измерение по SCD Type 1.","История не сохраняется."),
("gpe_24_scd2","Создайте SCD2 с valid_from/to,current flag.","Интервалы одного ключа не пересекаются."),
("gpe_25_fact_lookup","Свяжите факт с версией измерения по времени.","JOIN по business key и valid interval."),
("gpe_26_reconciliation","Соберите source/stage/target/reject reconciliation.","source=accepted+rejected и target delta."),
("gpe_27_failure","Смоделируйте ошибку после staging и сохраните FAILED.","Watermark/target должны остаться согласованными."),
("gpe_28_retry","Повторите failed batch безопасно.","Новая attempt или управляемое продолжение."),
("gpe_29_sla","Рассчитайте duration, throughput и SLA status.","Технические метрики — часть ETL."),
("gpe_30_pipeline","Создайте итоговый audit pipeline по всем этапам.","Каждый stage имеет counts,status,started/finished."),
]
def md(x): return nbf.v4.new_markdown_cell(x)
def code(x): return nbf.v4.new_code_cell(x)
cells=[
md("# ETL в Greenplum — 30 заданий\n\nЦель ETL — не просто перенести строки, а дать воспроизводимый, проверяемый и повторяемый результат. Все изменяемые объекты учебные и находятся в `m_razhin`."),
code("%load_ext sql\n%config SqlMagic.displaylimit = 150\n%sql postgresql+psycopg2://gpadmin@cbdb-coordinator:5432/moex"),
md("## 1. Слои\n\nRaw сохраняет полученный контракт и технические поля загрузки. Staging приводит типы/формат и отделяет ошибки. DDS хранит согласованные сущности и историю. DM оптимизируется под потребление. Слои не должны дублировать друг друга без ответственности."),
md("## 2. Batch и attempt\n\nBatch описывает логическую порцию данных, attempt — конкретную попытку. Повтор после сбоя может иметь тот же batch_id и новый attempt_no. Audit хранит start/end, status, counts, watermark и error."),
md("## 3. Атомарность\n\nПользователь не должен видеть половину загрузки. Транзакция объединяет target mutation и audit success. Но внешняя запись HDFS не всегда участвует в транзакции Greenplum, поэтому cross-system pipeline требует этапов и reconciliation."),
md("## 4. Full refresh\n\nПрост, когда target мал и допустимо полностью пересобрать. Опасный `TRUNCATE; INSERT` без транзакции создаёт окно пустых данных. Альтернативы: staging+swap/exchange или транзакционный replace."),
md("## 5. Incremental load\n\nIncrement выбирает только новые/изменённые строки. Watermark должен задавать строгий порядок. Один timestamp недостаточен при одинаковом времени; используют `(updated_at, id)` или устойчивый offset."),
md("## 6. Watermark lifecycle\n\nWatermark читается до extract, новая граница вычисляется из принятого batch, но фиксируется только после успешной target. Если продвинуть раньше, retry потеряет строки. Если не обеспечить идемпотентность, retry создаст дубли."),
md("## 7. Идемпотентность\n\nОдинаковый вход и batch должны приводить к одинаковому target. Это достигается ключами, staging, delete+insert заданного slice, exchange, upsert pattern и audit. Надежда «DAG не запустится дважды» не является гарантией."),
md("## 8. Late-arriving data\n\nСобытие может прийти позже watermark, но иметь старое business time. Варианты: overlap window с дедупликацией, отдельный correction feed, повтор периода или различение ingestion time/event time."),
md("## 9. Greenplum upsert\n\nЧасто используют staging: определить новые/changed keys, удалить соответствующие target rows и вставить канонические версии в одной транзакции. Массовый pattern лучше построчных UPDATE, особенно для AO."),
md("## 10. Hashdiff\n\nHash бизнес-атрибутов быстро отмечает изменение, но требует канонического порядка, формата типов и NULL marker. Hash collision теоретически возможна; критичные системы могут дополнительно сравнивать поля."),
md("## 11. Delete+insert slice\n\nДля факта с датой удобно переобрабатывать день/месяц: staging содержит полный slice, quality checks подтверждают его, затем target slice заменяется. Предикат DELETE и диапазон staging обязаны совпасть."),
md("## 12. Partition exchange\n\nExchange — быстрый вариант замены большого slice. ETL готовит физически совместимую staging и выполняет metadata operation после checks. Бывшая partition остаётся отдельной таблицей и требует управляемой очистки."),
md("## 13. Дедупликация\n\nОпределите business key, версию и tie-breaker. `DISTINCT` не выбирает правильную версию. Сохраняйте число входных версий и rejected conflicts для аудита."),
md("## 14. SCD\n\nType 1 перезаписывает атрибуты. Type 2 закрывает текущий интервал и создаёт новую surrogate version. Инварианты SCD2: одна current row на key, интервалы не пересекаются, valid_from<valid_to."),
md("## 15. Fact lookup\n\nФакт связывается с dimension version, действовавшей в event time: `event_ts>=valid_from AND event_ts<valid_to`. JOIN только с current row исторически неверен."),
md("## 16. Quality и severity\n\nERROR блокирует публикацию, WARN допускает загрузку с наблюдением, INFO описывает профиль. Правило хранит идентификатор, scope, measured, threshold и статус."),
md("## 17. Reconciliation\n\nSource rows = accepted + rejected. Stage accepted должно соответствовать target delta с учётом updates/deletes. Проверяют count, distinct keys, суммы, min/max и checksum."),
md("## 18. Failure и retry\n\nПри ошибке сохраняют FAILED, SQLSTATE/message и этап. Target/watermark откатываются согласованно. Retry повторяет весь зависимый участок и не опирается на частично сохранённые временные данные без проверки."),
md("## 19. Производительность\n\nBulk insert, совместимое распределение staging/target, AO storage и обработка partition slice уменьшают Motion и bloat. ANALYZE выполняют после значимой загрузки до потребительских запросов."),
md("## 20. Порядок практики\n\nContract→batch audit→extract raw→typed staging→quality/rejects→dedup/change detection→target transaction→watermark→ANALYZE→reconciliation→publish success."),
]
for n,(obj,prompt,hint) in enumerate(tasks,1):
    if n==11: cells.append(md("## Уровень 2 — incremental, late data и reload"))
    if n==21: cells.append(md("## Уровень 3 — dedup, SCD, failure/retry и SLA"))
    cells += [md(f"### Задание {n}. `m_razhin.{obj}`\n\n**Что сделать:** {prompt}\n\nСохраняйте измеримый результат и audit. Повторный запуск задания не должен портить target.\n\n<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"),
      code(f"%%sql\nSET search_path TO m_razhin,public;\n-- Реализуйте m_razhin.{obj}."),
      code("%%sql\n-- Ручная проверка counts/checksum/idempotency."),
      code(f"%%sql\nSELECT * FROM greenplum_training.run_checks('etl',{n});")]
cells += [md("## Прогресс"),code("%%sql\nSELECT * FROM greenplum_training.progress WHERE module_name='etl' ORDER BY task_no;")]
nb=nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3 (ipykernel)","language":"python","name":"python3"}})
OUTPUT.parent.mkdir(parents=True,exist_ok=True); nbf.write(nb,OUTPUT); print(OUTPUT)
