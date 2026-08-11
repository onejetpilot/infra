from pathlib import Path
import nbformat as nbf
R=Path(__file__).resolve().parent.parent
M={
'01_foundations_30_Tasks.ipynb':('Архитектура Spark','Driver создаёт logical work и планирует jobs; executors выполняют tasks. Action материализует ленивый lineage, wide dependency разделяет stages shuffle-границей.','Рисуйте application→jobs→stages→tasks и связывайте каждый task с одной input partition.'),
'02_dataframes_30_Tasks.ipynb':('DataFrame API','DataFrame — неизменяемый logical plan с schema. Встроенные Column expressions видимы Catalyst; типы и NULL определяют семантику до исполнения.','После каждого смыслового шага проверяйте schema и план, но не запускайте лишний полный count.'),
'03_spark_sql_30_Tasks.ipynb':('Spark SQL','SQL и DataFrame компилируются одним Catalyst. Temp view принадлежит session, Hive table — Metastore/HDFS; DDL задаёт lifecycle и physical layout.','Сравнивайте SQL/DataFrame plans и подтверждайте catalog, LOCATION, partitions и результат.'),
'04_analytics_30_Tasks.ipynb':('JOIN, агрегации и окна','GroupBy и крупный JOIN обычно создают shuffle. Broadcast переносит малую сторону. Window сохраняет grain, но требует partition/order/frame и часто сортировки.','Докажите cardinality до JOIN, используйте предагрегацию и сверяйте ключи/суммы после.'),
'05_storage_30_Tasks.ipynb':('Хранение Spark','Spark partition — единица task, Hive partition — каталог. Parquet row groups/statistics обеспечивают pruning/pushdown, а число выходных файлов управляется распределением перед write.','Измеряйте input/output files, partitions, bytes, codec, schema и scan plan; не судите по имени метода.'),
'06_performance_30_Tasks.ipynb':('Производительность','Catalyst строит optimized logical и physical plan; AQE использует runtime statistics. Exchange, Sort, spill, skew и Python UDF объясняют основную стоимость.','Сначала baseline и correctness, затем один change, повторный benchmark и plan evidence.'),
'07_quality_etl_30_Tasks.ipynb':('Качество и ETL','Data contract превращается в DataFrame assertions. Accepted/reject, run metadata, watermark и reconciliation формируют управляемый batch, а не просто write.','Докажите schema, NULL/domain/key, read=accepted+rejected, target delta и rerun.'),
'08_capstone_30_Tasks.ipynb':('Итоговый Spark-проект','Data product объединяет grain/schema, layers, DQ, physical design, plan, incremental strategy и runbook. Код без доказательств идемпотентности и reconciliation не закончен.','Принимайте каждый слой отдельно и сохраняйте explain/metrics/files вместе с бизнес-проверками.')}
ARCH='''```text
transformations → unresolved logical plan
       ↓ analysis (catalog/types)
   optimized logical plan (Catalyst)
       ↓ physical planning / AQE
job → stage → shuffle → stage
       tasks             tasks
       └──── executors ─────┘
```
Action создаёт job. Один notebook/application может породить много jobs, а один job —
несколько stages. `repartition`, join и groupBy часто добавляют Exchange.'''
EBAY='''Grain eBay — `itemid` в `snapshot_dt`; 2 501 511 строк, 24 колонки, Parquet/Snappy.
Partition column — дата снимка. Цена, продавец, категории и доставка денормализованы.
Перед `latest item` или dedup проверяйте уникальность пары и задавайте tie-breaker.'''
def md(x):return nbf.v4.new_markdown_cell(x)
for p in sorted((R/'notebooks').glob('*_30_Tasks.ipynb')):
 if p.name not in M:continue
 nb=nbf.read(p,4);title,model,method=M[p.name]
 nb.cells=[c for c in nb.cells if c.metadata.get('theory_enhancer')!='spark-v1']
 xs=[md(f'## Результаты обучения\n\nПосле **{title}** вы должны объяснить transformation как plan, предсказать action/jobs/shuffle, связать schema/grain с результатом и доказать физическую эффективность через explain/UI/metrics.'),md(f'## Ментальная модель исполнения\n\n{model}\n\n{ARCH}'),md(f'## Данные eBay\n\n{EBAY}\n\nПолная схема и проверки качества находятся в `data-catalog`. Raw read-only, результаты — в личном `spark_training`.'),md(f'## Алгоритм решения\n\n1. Зафиксируйте входной и целевой grain. 2. Выберите только нужные columns/rows. 3. Соберите transformation без action. 4. Проверьте schema и explain. 5. Предскажите partitions/shuffle. 6. Выполните минимальный action/write. 7. Повторно прочитайте и сверяйте keys/metrics. 8. Сохраните evidence.\n\n{method}'),md('## Типичные ошибки\n\n- Вызывать count/show после каждого шага и создавать лишние jobs.\n- Использовать Python UDF при наличии встроенной функции.\n- Делать repartition без понимания Exchange и целевого файла.\n- Broadcast большой стороны или collect на driver.\n- Кэшировать одноразовый DataFrame без materialization/unpersist.\n- Измерять скорость при разных результатах или непрогретом JVM.'),md('## Самопроверка\n\n1. Какой action создаёт job? 2. Где появится shuffle? 3. Сколько input/output partitions? 4. Видит ли Catalyst выражение? 5. Каков grain после JOIN/window? 6. Как проверить idempotent rerun?')]
 for c in xs:c.metadata['theory_enhancer']='spark-v1'
 nb.cells[1:1]=xs
 for c in nb.cells:
  if c.cell_type=='markdown' and c.source.startswith('### Задание ') and '<!-- task-card-spark-v1 -->' not in c.source:
   c.source+='''

<!-- task-card-spark-v1 -->
#### Карточка выполнения

- **Учебная цель:** какой Spark-механизм должен стать наблюдаемым?
- **Контракт данных:** входной/целевой grain, key, schema, NULL и ожидаемый объём.
- **Логический план:** projection, filters, joins, aggregates/windows до action.
- **Физический прогноз:** partitions, Exchange, sort, broadcast, jobs/stages.
- **Проверка:** `printSchema`, `explain("formatted")`, keys/metrics и повторное чтение Parquet.
- **Эксплуатация:** write mode, file count, повтор запуска, cleanup/unpersist.
- **Evidence/checker:** объясните наблюдаемый plan и результат, а не просто вызванный API.

Подсказка не определяет готовую цепочку transformations: её нужно вывести из grain и контракта.'''
 for c in nb.cells:
  if c.cell_type=='code':c.outputs=[];c.execution_count=None
 nbf.write(nb,p)
