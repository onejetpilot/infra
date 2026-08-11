from pathlib import Path
import nbformat as nbf
R=Path(__file__).resolve().parent.parent
M={
'01_hdfs_model_30_Tasks.ipynb':('Архитектура HDFS','NameNode хранит namespace и block map, DataNode хранит bytes. Клиент получает адреса блоков и читает/пишет DataNode напрямую; replication защищает от потери узла, но не от логического удаления.','Сопоставляйте каждую команду с изменением namespace, block metadata и физическими replicas.'),
'02_hdfs_cli_30_Tasks.ipynb':('HDFS CLI','`hdfs dfs` работает с удалённым namespace. Exit code важнее красивого stdout; URI, glob, Trash и права определяют область изменения.','До команды разрешите абсолютный HDFS path, после используйте независимые test/stat/count/du/checksum.'),
'03_formats_30_Tasks.ipynb':('Форматы и Parquet','Parquet организует row groups → column chunks → pages; footer хранит schema/statistics. Projection и predicate pushdown уменьшают I/O, compression меняет CPU/size.','Измеряйте schema, codec, row groups, число/размер файлов и читаемость нужных columns/predicates.'),
'04_hive_ddl_30_Tasks.ipynb':('Hive DDL','Hive Metastore хранит schema, LOCATION и partitions, а строки лежат в HDFS. Managed/external различаются владением lifecycle; schema-on-read не исправляет несовместимые типы.','Разделяйте metadata operation и file operation, подтверждайте SHOW CREATE/DESCRIBE и HDFS ls/count.'),
'05_partitioning_30_Tasks.ipynb':('Партиционирование Hive','Hive partition — каталог, зарегистрированный в Metastore. Pruning исключает каталоги только при распознаваемом предикате; высокая cardinality создаёт metadata/small-files проблему.','Доказывайте pruning через EXPLAIN и input paths, а дизайн — числом partitions/files/bytes.'),
'06_operations_30_Tasks.ipynb':('Права и эксплуатация','Доступ требует execute на каждом родительском каталоге и permission/ACL на цели. Health включает capacity, live DataNodes, replication, corrupt blocks, quotas и recoverability.','Фиксируйте observed state, threshold, diagnosis, safe action и повторную проверку; chmod 777 запрещён как ответ.'),
'07_etl_quality_30_Tasks.ipynb':('Batch ETL и качество','Raw сохраняет вход, staging типизирует, accepted/reject объясняют судьбу строки, publish происходит после reconciliation. Watermark обновляется только после успешного batch.','Для каждой порции докажите read=accepted+rejected, key uniqueness, target delta и idempotent rerun.'),
'08_capstone_30_Tasks.ipynb':('Итоговый Hadoop-проект','Завершённый data product объединяет contract, HDFS layout, Hive schema, partitions, quality, permissions, update strategy и runbook.','Принимайте проект доказательствами: schema, counts, keys, files, pruning, rights, replication и повтор дня.')}
ARCH='''```text
client ── metadata RPC ──► NameNode
  │                         │ block locations
  └── data stream ──► DataNode 1 ──► DataNode 2

HiveServer2 ──► Metastore (schema/location/partitions)
      └──────► execution engine ──► HDFS files
```
NameNode не хранит содержимое файла, а Metastore не хранит строки таблицы.'''
EBAY='''```text
/data/raw/ebay/
├── snapshot_dt=2026-06-24/part-....snappy.parquet
├── snapshot_dt=2026-06-25/part-....snappy.parquet
└── ...
```
Grain: наблюдение `itemid` в `snapshot_dt`. Группы колонок: карточка/цена,
иерархия категорий, продавец, география и доставка. Полная schema — в `data-catalog`.'''
def md(x):return nbf.v4.new_markdown_cell(x)
for p in sorted((R/'notebooks').glob('*_30_Tasks.ipynb')):
 if p.name not in M:continue
 nb=nbf.read(p,4);title,model,method=M[p.name]
 nb.cells=[c for c in nb.cells if c.metadata.get('theory_enhancer')!='hadoop-v1']
 xs=[md(f'## Результаты обучения\n\nПосле **{title}** вы должны объяснить внутренний механизм, предсказать изменения metadata/files, выбрать безопасную команду и доказать итог измерением, а не сообщением об успехе.'),md(f'## Архитектурная модель\n\n{model}\n\n{ARCH}'),md(f'## Физическая схема eBay\n\n{EBAY}\n\nОбщий raw read-only; результаты принадлежат `/user/$HDFS_USER/hadoop_training` и личной Hive DB.'),md(f'## Алгоритм исследования\n\n1. Зафиксируйте path/URI, owner и ожидаемый объект. 2. Снимите состояние до. 3. Выполните одно изменение. 4. Проверьте exit code. 5. Измерьте namespace/files/bytes/schema/rows. 6. Повторите команду и оцените идемпотентность. 7. Сохраните evidence.\n\n{method}'),md('## Типичные ошибки\n\n- Путать локальный путь с HDFS URI.\n- Делать вывод по `ls`, не проверяя blocks/bytes/schema.\n- Использовать root или 777 вместо модели доступа.\n- Создавать partition-каталог без Metastore или metadata без файлов.\n- Считать replication резервной копией.\n- Игнорировать малые файлы и цену NameNode metadata.'),md('## Самопроверка\n\n1. Какие metadata изменятся? 2. Где физически лежат bytes? 3. Сколько logical и physical bytes? 4. Кто может читать/писать? 5. Что произойдёт при повторе? 6. Какая независимая команда опровергнет вывод?')]
 for c in xs:c.metadata['theory_enhancer']='hadoop-v1'
 nb.cells[1:1]=xs
 for c in nb.cells:
  if c.cell_type=='markdown' and c.source.startswith('### Задание ') and '<!-- task-card-hadoop-v1 -->' not in c.source:
   c.source+='''

<!-- task-card-hadoop-v1 -->
#### Карточка выполнения

- **Цель:** объясните HDFS/Hive/Parquet-механизм задания.
- **Вход:** укажите URI, формат, owner, grain и объём.
- **Выход:** точный path/table, lifecycle и ожидаемые files/rows.
- **До/после:** снимите `test/stat/count/du/getfacl`, schema или EXPLAIN по теме.
- **Безопасность:** работайте только в личном каталоге; raw не изменяется.
- **Повтор:** сформулируйте, почему второй запуск безопасен или чем он отличается.
- **Evidence/checker:** сохраните фактическую команду, наблюдение и причинное объяснение.

Созданный пустой каталог и текст «команда сработала» не доказывают выполнение.'''
 for c in nb.cells:
  if c.cell_type=='code':c.outputs=[];c.execution_count=None
 nbf.write(nb,p)
