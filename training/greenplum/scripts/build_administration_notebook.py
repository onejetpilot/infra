import os
from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parent.parent
OUTPUT=Path(os.environ.get("GREENPLUM_ADMIN_OUTPUT",ROOT/"notebooks"/"08_Administration_30_Tasks.ipynb"))
tasks=[
("gpa_01_topology","Создайте VIEW полной топологии content/primary/mirror/standby.","gp_segment_configuration."),
("gpa_02_health","Создайте сводку up/down и sync mode.","Нормальное состояние: все u, mirrors s."),
("gpa_03_role_drift","Найдите несовпадение role/preferred_role.","После failover роли могут отличаться."),
("gpa_04_host_balance","Покажите число primary/mirror по host.","Fault domains должны быть разнесены."),
("gpa_05_version","Создайте VIEW версии и ключевых extensions.","PXF/gp_toolkit обязательны для курса."),
("gpa_06_sessions","Создайте безопасный VIEW активных сессий.","Не показывайте пароль/секреты query text."),
("gpa_07_long_queries","Найдите активные запросы дольше порога.","Различайте query_start и xact_start."),
("gpa_08_idle_tx","Найдите idle in transaction.","Они удерживают snapshot/locks."),
("gpa_09_locks","Создайте VIEW ожидающих блокировки.","Свяжите pg_locks и activity."),
("gpa_10_blockers","Постройте blocked→blocker mapping.","Используйте blocking pids/lock keys."),
("gpa_11_schema_sizes","Суммируйте размер таблиц по schema.","Partition leaves учитывать отдельно/без double count."),
("gpa_12_table_sizes","Покажите крупнейшие учебные таблицы.","Строки, bytes, storage, policy."),
("gpa_13_segment_sizes","Покажите размер выбранной таблицы по сегментам.","Ищите byte skew."),
("gpa_14_skew","Рассчитайте row/byte skew учебных таблиц.","Пустые segments тоже учитываются."),
("gpa_15_bloat","Оцените bloat/hidden tuples доступными метриками.","Метод зависит от heap/AO."),
("gpa_16_stats_age","Покажите отсутствие/свежесть статистики.","После load нужен ANALYZE."),
("gpa_17_analyze","Выполните ANALYZE учебной таблицы и зафиксируйте эффект.","Не запускайте cluster-wide без причины."),
("gpa_18_vacuum","Выполните безопасный VACUUM учебной heap и сохраните метрики.","VACUUM не аналог full rewrite."),
("gpa_19_ao_stats","Создайте VIEW AO auxiliary metadata.","pg_appendonly, visimap/segfiles."),
("gpa_20_partitions","Найдите excessive/small partitions.","Планирование страдает от тысяч leaf."),
("gpa_21_resource_groups","Создайте VIEW resource groups и limits.","Не изменяйте production-like defaults."),
("gpa_22_memory","Покажите statement_mem/resource context текущей сессии.","Параметры действуют на разных уровнях."),
("gpa_23_spill","Создайте VIEW spill workfiles текущих/последних запросов.","Используйте gp_toolkit."),
("gpa_24_cancel","Безопасно отмените только созданный учебный запрос.","Сначала PID и ownership."),
("gpa_25_terminate","Зафиксируйте отличие cancel и terminate.","Terminate закрывает session."),
("gpa_26_pxf","Сводка PXF extension/server/path readiness.","Оба segment hosts."),
("gpa_27_hdfs","Сводка NameNode/DataNode и персонального каталога.","Не изменяйте системные HDFS paths."),
("gpa_28_incident","Создайте incident report для медленного запроса.","Plan,skew,motion,spill,blocker,stats."),
("gpa_29_runbook","Создайте VIEW шагов runbook для типовых симптомов.","Симптом→проверка→безопасное действие→эскалация."),
("gpa_30_dashboard","Создайте итоговый health dashboard курса.","Cluster,queries,storage,stats,PXF,HDFS."),
]
def md(x): return nbf.v4.new_markdown_cell(x)
def code(x): return nbf.v4.new_code_cell(x)
cells=[
md("# Администрирование Cloudberry / Greenplum — 30 заданий\n\nМодуль учит диагностировать кластер без опасных изменений. Любые cancel/terminate/vacuum выполняются только на собственной учебной сессии или таблице."),
code("%load_ext sql\n%config SqlMagic.displaylimit = 200\n%sql postgresql+psycopg2://gpadmin@cbdb-coordinator:5432/moex"),
md("## 1. Область ответственности\n\nАдминистрирование включает доступность, производительность, ёмкость, безопасность и восстановление. Диагностика начинается с наблюдения и сбора evidence; случайный restart или terminate может скрыть причину и усугубить инцидент."),
md("## 2. Топология\n\nContent — логический сегмент. Primary обслуживает запросы, mirror синхронно поддерживает копию. Standby защищает coordinator. `role` — текущая роль, `preferred_role` — исходная. Status `u` и mode `s` — нормальное синхронное состояние."),
md("## 3. Fault domains\n\nPrimary и его mirror должны находиться на разных host/failure domains. Баланс primary по host влияет на нормальную нагрузку и состояние после failover."),
md("## 4. Failover\n\nПри недоступности primary mirror может получить роль primary. После восстановления требуется вернуть redundancy/resync. Учебный курс не инициирует failover автоматически, потому что контейнеры содержат локальное состояние."),
md("## 5. Сессия, запрос, транзакция\n\n`pg_stat_activity` различает backend session, текущий query и transaction. Долгий query может быть нормальным ETL; idle in transaction бездействует, но удерживает snapshot/locks. Сравнивайте query_start и xact_start."),
md("## 6. Блокировки\n\nBlocking — нормальный механизм согласованности, пока ожидание ограничено. Диагностика строит цепочку blocked→blocker, тип/объект lock и возраст транзакции. Удаляют причину, а не обязательно самую заметную жертву."),
md("## 7. Cancel и terminate\n\nCancel просит отменить текущий statement, сохраняя session. Terminate завершает backend и откатывает транзакцию. Сначала проверяют PID, user, query, transaction и downstream impact. Никогда не применяйте к неизвестной сессии по одному возрасту."),
md("## 8. Размер\n\nЛогический размер таблицы распределён по сегментам. Partition parent может почти не иметь данных, а leaves — занимать весь объём. Не суммируйте parent и leaves одновременно. Отдельно учитывайте indexes/AO auxiliary."),
md("## 9. Skew\n\nRow skew влияет на CPU/число операций, byte skew — на I/O/ёмкость. Следите за трендом: растущий skew может появиться из-за изменения данных без изменения DDL."),
md("## 10. Heap bloat\n\nMVCC оставляет dead tuples до vacuum. `VACUUM` делает место повторно используемым, но обычно не возвращает файл ОС. Rewrite/VACUUM FULL намного тяжелее и требует отдельного планирования."),
md("## 11. AO maintenance\n\nAO использует segment files, visibility map и auxiliary metadata. Частые UPDATE/DELETE создают невидимые строки. Диагностика AO отличается от heap; не применяйте heap-only формулу bloat."),
md("## 12. Statistics\n\nОтсутствующая/устаревшая статистика ухудшает cardinality и план. ANALYZE запускают после существенной загрузки и отслеживают нужные колонки. Cluster-wide analyze может быть дорогим."),
md("## 13. Resource management\n\nResource groups ограничивают concurrency, CPU и memory. Statement memory влияет на hash/sort/aggregate, но является частью общего бюджета. Увеличение одной сессии может ухудшить кластер для остальных."),
md("## 14. Spill\n\nWorkfile создаётся, когда оператор не помещается в память. Небольшой spill допустим; массовый spill замедляет запрос и заполняет диск. Лечение: статистика, уменьшение/проекция данных, physical design, join order или обоснованная память."),
md("## 15. Capacity\n\nСледят за ростом данных, свободным местом каждого host, количеством files/partitions, временными файлами и HDFS. Среднее свободное место скрывает переполненный segment host."),
md("## 16. PXF/HDFS\n\nSQL extension может быть установлено, но PXF server остановлен или Hadoop config/path недоступны. Проверка идёт слоями: extension→server 5888 на обоих hosts→NameNode→DataNode→permissions/path→format."),
md("## 17. Инцидент\n\nСначала timestamp/scope/symptom, затем cluster health, blockers, plan, actual rows/skew, Motion, spill, statistics и recent changes. После mitigation сохраняют root cause и preventive action."),
md("## 18. Runbook\n\nRunbook содержит безопасные read-only проверки, критерии решений, команды с областью действия, rollback и момент эскалации. Команда без предусловий — не runbook."),
md("## 19. Мониторинг\n\nDashboard показывает состояние, но alert должен быть actionable. Метрики: unavailable instances, replication mode, query age, idle tx, blockers, storage/skew, stats gaps, spill, PXF/HDFS."),
md("## 20. Безопасность упражнений\n\nНе останавливайте сегменты, не удаляйте data directories, не меняйте cluster configs и не завершайте чужие backend. Все destructive experiments ограничиваются `greenplum_training.admin_lab` и собственными сессиями."),
]
for n,(obj,prompt,hint) in enumerate(tasks,1):
    if n==11: cells.append(md("## Уровень 2 — storage, skew и maintenance"))
    if n==21: cells.append(md("## Уровень 3 — resources, external health и incident response"))
    cells += [md(f"### Задание {n}. `m_razhin.{obj}`\n\n**Что сделать:** {prompt}\n\nСначала выполните read-only диагностику. Любое действие укажите с точным target и сохраните before/after evidence.\n\n<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"),
      code(f"%%sql\nSET search_path TO m_razhin,public;\n-- Создайте m_razhin.{obj}."),
      code("%%sql\n-- Ручная проверка диагностического результата."),
      code(f"%%sql\nSELECT * FROM greenplum_training.run_checks('administration',{n});")]
cells += [md("## Прогресс"),code("%%sql\nSELECT * FROM greenplum_training.progress WHERE module_name='administration' ORDER BY task_no;")]
nb=nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3 (ipykernel)","language":"python","name":"python3"}})
OUTPUT.parent.mkdir(parents=True,exist_ok=True); nbf.write(nb,OUTPUT); print(OUTPUT)
