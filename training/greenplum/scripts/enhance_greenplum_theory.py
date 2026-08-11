from pathlib import Path
import nbformat as nbf
R=Path(__file__).resolve().parent.parent
M={
'01_Distribution_30_Tasks.ipynb':('Распределение и skew','Строки физически принадлежат сегментам. DISTRIBUTED BY вычисляет hash ключа, RANDOMLY распределяет без colocated JOIN, REPLICATED копирует малый справочник.','Yandex Metrica: visit grain, фильтры date/country/city/ip','Профилируйте cardinality и heavy hitters, измерьте rows по gp_segment_id и skew=max/avg; затем оцените Motion в реальном JOIN.'),
'02_Storage_Partitioning_30_Tasks.ipynb':('Хранение и партиционирование','Heap, AO row и AOCO оптимальны для разных write/read patterns. Compression и column orientation уменьшают I/O, partition pruning ограничивает физические дочерние таблицы.','Metrica по дате и учебные AO/AOCO таблицы','Выберите storage по workload, partition key по регулярному фильтру, разумную гранулярность и докажите pruning через EXPLAIN.'),
'03_Query_Plans_Optimization_30_Tasks.ipynb':('Планы и Motion','План Greenplum — дерево локальных operators и межсегментных Motion. Redistribute меняет hash, Broadcast копирует сторону, Gather возвращает coordinator.','Metrica и контролируемые таблицы с разным distribution','Сначала сравните estimated/actual rows, затем найдите Motion и объём строк через него; исправляйте статистику, distribution или форму JOIN по одной причине.'),
'04_GPFDIST_30_Tasks.ipynb':('GPFDIST','gpfdist — параллельный HTTP transport: сегменты читают разные части внешнего файла. External table хранит metadata формата и LOCATION, а reject limit определяет отношение к плохим строкам.','countries.csv и учебные CSV/PSV файлы','Проверьте доступность URI из segment network, delimiter/quote/header/encoding, профиль reject и reconciliation external→internal.'),
'05_PXF_HDFS_Parquet_30_Tasks.ipynb':('PXF, HDFS и Parquet','PXF запускает fragment work рядом с сегментами и преобразует HDFS/Parquet в строки Greenplum. Projection и predicate pushdown определяют, сколько данных покинет HDFS.','Yandex Metrica и MOEX Parquet в HDFS','Сверьте PXF profile и LOCATION, типы с Parquet schema, узкую projection, partition filter и число строк с Hive/Spark.'),
'06_ETL_30_Tasks.ipynb':('Распределённый ETL','ETL в MPP должен сохранять не только строки, но distribution, partitions, statistics и повторяемость. Staging изолирует вход, exchange/swap сокращает окно публикации.','учебные staging/core, Metrica и справочники','Определите batch key, full/incremental boundary, rejects, reconciliation, publish transaction и ANALYZE после изменения.'),
'07_Data_Marts_30_Tasks.ipynb':('Факты, измерения и витрины','Grain факта определяет ключи и аддитивность. В MPP collocation факта с крупным JOIN важнее случайного «равномерного» ключа; малые dimensions можно реплицировать.','MOEX trade grain, ticker/day/deal type','Сформулируйте grain сделки, детерминированно ранжируйте BUY/SELL, проектируйте dimensions и сверяйте витрину с raw по ключам и VALUE.'),
'08_Administration_30_Tasks.ipynb':('Эксплуатация Greenplum','Кластер считается здоровым, когда доступны coordinator, segments и interconnect, нет skew/долгих блокировок, статистика и bloat контролируются, а recovery проверен.','системные views gp_segment_configuration, pg_stat_activity и catalog','Соберите наблюдение, порог, диагноз и безопасное действие. Runbook обязан содержать проверку до и после, а не только команду.')}
ARCH='''```text
client → coordinator (parse/optimize)
              │ dispatch slices
       ┌──────┼──────┐
       ▼      ▼      ▼
    segment segment segment
       └── Motion/interconnect ──┘
              │
              ▼
          coordinator
```
Coordinator не должен становиться местом обработки всех строк. Хороший план оставляет
scan/aggregate на сегментах и перемещает только необходимое.'''
def md(x):return nbf.v4.new_markdown_cell(x)
for p in sorted((R/'notebooks').glob('*.ipynb')):
 if p.name not in M:continue
 nb=nbf.read(p,4);title,model,data,method=M[p.name]
 nb.cells=[c for c in nb.cells if c.metadata.get('theory_enhancer')!='gp-v1']
 xs=[md(f'## Результаты обучения\n\nПосле **{title}** вы должны объяснять физическое выполнение на coordinator/segments, связывать logical SQL с Motion/I/O/skew, выбирать дизайн по workload и доказывать решение измерениями.'),md(f'## Ментальная модель\n\n{model}\n\n{ARCH}'),md(f'## Данные и grain\n\n{data}. Полные схемы находятся в `data-catalog`. Общие external/raw объекты читаются, учебные результаты создаются только в `m_razhin`.'),md(f'## Инженерный алгоритм\n\n1. Назовите grain и ключ. 2. Оцените объём/cardinality. 3. Выберите distribution/storage/partition. 4. Предскажите Motion и I/O. 5. Создайте минимальный объект. 6. ANALYZE. 7. Снимите EXPLAIN и сегментные метрики. 8. Сверьте результат.\n\n{method}'),md('## Типичные ошибки\n\n- Переносить правила PostgreSQL без учёта MPP.\n- Выбирать distribution key только по высокой cardinality.\n- Путать partitioning с distribution.\n- Считать Broadcast всегда плохим, а Redistribute всегда допустимым.\n- Сравнивать время единственного запуска без rows/Motion/I/O.\n- Создавать external object с путём, доступным Windows, но не сегментам.'),md('## Вопросы для самопроверки\n\n1. Где физически лежит строка? 2. Какие slices выполнят сегменты? 3. Что и сколько передаёт Motion? 4. Как проявится skew? 5. Что произойдёт при повторной загрузке? 6. Как доказать результат из независимого источника?')]
 for c in xs:c.metadata['theory_enhancer']='gp-v1'
 nb.cells[1:1]=xs
 for c in nb.cells:
  if c.cell_type=='markdown' and c.source.startswith('### Задание ') and '<!-- task-card-gp-v1 -->' not in c.source:
   c.source+='''

<!-- task-card-gp-v1 -->
#### Карточка выполнения

- **Учебная цель:** назовите распределённый механизм, который демонстрирует задание.
- **Вход/выход:** зафиксируйте grain, ключ, объём и владельца объекта.
- **Физический прогноз:** distribution, partitions, scan, Motion и ожидаемый bottleneck.
- **Порядок:** профиль → DDL/SQL → ANALYZE → EXPLAIN/метрики → reconciliation → checker.
- **Граничные случаи:** пустой вход, NULL ключа, heavy hitter, повтор запуска и недоступный segment source.
- **Checker:** прочитайте название каждой проверки и объясните, какой инвариант она доказывает.

Подсказка задаёт направление исследования, но не готовое распределение, DDL или запрос.'''
 for c in nb.cells:
  if c.cell_type=='code':c.outputs=[];c.execution_count=None
 nbf.write(nb,p)
