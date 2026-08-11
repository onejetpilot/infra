DROP TABLE IF EXISTS greenplum_training.storage_source;
CREATE TABLE greenplum_training.storage_source
WITH (appendoptimized=true, orientation=row, compresstype=zstd, compresslevel=1)
AS
SELECT * FROM greenplum_training.dist_source
DISTRIBUTED BY (event_id);
ANALYZE greenplum_training.storage_source;

DELETE FROM greenplum_training.task_tests
WHERE module_name='storage_partitioning';

INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql)
SELECT 'storage_partitioning',n,1,'Объект создан с точным именем',
       format('SELECT greenplum_training.relation_exists(%L)::text',
              format('m_razhin.gps_%s_%s',lpad(n::text,2,'0'),suffix)),
       'SELECT true::text'
FROM (VALUES
(1,'heap'),(2,'ao_row'),(3,'ao_column'),(4,'ao_zlib'),(5,'ao_zstd'),
(6,'ao_rle'),(7,'storage_catalog'),(8,'table_sizes'),
(9,'compression_ratio'),(10,'scan_benchmark'),(11,'range_partition'),
(12,'partition_catalog'),(13,'partition_counts'),(14,'pruning_plan'),
(15,'no_pruning'),(16,'default_partition'),(17,'add_partition'),
(18,'drop_partition'),(19,'truncate_partition'),(20,'split_default'),
(21,'staging_like'),(22,'stage_latest'),(23,'change_key'),
(24,'add_exchange_target'),(25,'exchange_without_validation'),
(26,'exchange_counts'),(27,'exchange_metadata'),(28,'multilevel'),
(29,'partition_skew'),(30,'recommendation')) x(n,suffix);

INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql) VALUES
('storage_partitioning',1,2,'Heap не зарегистрирован как AO',
 $$SELECT (NOT EXISTS(SELECT 1 FROM pg_appendonly WHERE relid='m_razhin.gps_01_heap'::regclass)
 AND (SELECT count(*) FROM m_razhin.gps_01_heap)=100000)::text$$,
 $$SELECT true::text$$),
('storage_partitioning',2,2,'AO row без сжатия',
 $$SELECT (NOT columnstore AND compresstype='none' AND
 (SELECT count(*) FROM m_razhin.gps_02_ao_row)=100000)::text
 FROM pg_appendonly WHERE relid='m_razhin.gps_02_ao_row'::regclass$$,
 $$SELECT true::text$$),
('storage_partitioning',3,2,'AO column без сжатия',
 $$SELECT (columnstore AND compresstype='none' AND
 (SELECT count(*) FROM m_razhin.gps_03_ao_column)=100000)::text
 FROM pg_appendonly WHERE relid='m_razhin.gps_03_ao_column'::regclass$$,
 $$SELECT true::text$$),
('storage_partitioning',4,2,'AO column zlib level 5',
 $$SELECT (columnstore AND compresstype='zlib' AND compresslevel=5 AND
 (SELECT count(*) FROM m_razhin.gps_04_ao_zlib)=100000)::text
 FROM pg_appendonly WHERE relid='m_razhin.gps_04_ao_zlib'::regclass$$,
 $$SELECT true::text$$),
('storage_partitioning',5,2,'AO column zstd level 5',
 $$SELECT (columnstore AND compresstype='zstd' AND compresslevel=5 AND
 (SELECT count(*) FROM m_razhin.gps_05_ao_zstd)=100000)::text
 FROM pg_appendonly WHERE relid='m_razhin.gps_05_ao_zstd'::regclass$$,
 $$SELECT true::text$$),
('storage_partitioning',6,2,'AO column RLE',
 $$SELECT (columnstore AND lower(compresstype::text) IN ('rle_type','rle') AND
 (SELECT count(*) FROM m_razhin.gps_06_ao_rle)=100000)::text
 FROM pg_appendonly WHERE relid='m_razhin.gps_06_ao_rle'::regclass$$,
 $$SELECT true::text$$);

INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql) VALUES
('storage_partitioning',7,2,'Каталог описывает шесть вариантов',
 $$SELECT (count(*)=6 AND count(DISTINCT table_name)=6
 AND bool_and(storage_type IS NOT NULL))::text
 FROM m_razhin.gps_07_storage_catalog$$,
 $$SELECT true::text$$),
('storage_partitioning',8,2,'Размеры измерены на одинаковых данных',
 $$SELECT (count(*)=6 AND min(total_size_bytes)>0
 AND min(rows_count)=100000 AND max(rows_count)=100000)::text
 FROM m_razhin.gps_08_table_sizes$$,
 $$SELECT true::text$$),
('storage_partitioning',9,2,'Compression ratio рассчитан для шести вариантов',
 $$SELECT (count(*)=6 AND min(compression_ratio)>0
 AND abs(max(compression_ratio) FILTER(WHERE table_name='gps_01_heap')-1)<0.001)::text
 FROM m_razhin.gps_09_compression_ratio$$,
 $$SELECT true::text$$),
('storage_partitioning',10,2,'Benchmark содержит несколько повторов и вариантов',
 $$SELECT (count(DISTINCT table_name)>=3 AND count(*)>=9
 AND min(elapsed_ms)>=0)::text FROM m_razhin.gps_10_scan_benchmark$$,
 $$SELECT true::text$$),
('storage_partitioning',11,2,'Range table содержит все строки и leaf partitions',
 $$SELECT ((SELECT count(*) FROM m_razhin.gps_11_range_partition)=100000
 AND (SELECT count(*)>=3 FROM pg_partition_tree(
 'm_razhin.gps_11_range_partition'::regclass) WHERE isleaf))::text$$,
 $$SELECT true::text$$),
('storage_partitioning',12,2,'Каталог отражает фактическое дерево',
 $$SELECT (count(*)=(SELECT count(*) FROM pg_partition_tree(
 'm_razhin.gps_11_range_partition'::regclass))
 AND bool_or(is_leaf))::text FROM m_razhin.gps_12_partition_catalog$$,
 $$SELECT true::text$$),
('storage_partitioning',13,2,'Сумма leaf counts равна parent',
 $$SELECT (sum(rows_count)=100000
 AND count(*)=(SELECT count(*) FROM pg_partition_tree(
 'm_razhin.gps_11_range_partition'::regclass) WHERE isleaf))::text
 FROM m_razhin.gps_13_partition_counts$$,
 $$SELECT true::text$$),
('storage_partitioning',14,2,'Прямой диапазон использует одну partition',
 $$SELECT (scanned_partitions=1)::text FROM m_razhin.gps_14_pruning_plan$$,
 $$SELECT true::text$$),
('storage_partitioning',15,2,'Несаргабельный вариант не лучше прямого',
 $$SELECT (scanned_partitions>=(SELECT scanned_partitions
 FROM m_razhin.gps_14_pruning_plan))::text FROM m_razhin.gps_15_no_pruning$$,
 $$SELECT true::text$$),
('storage_partitioning',16,2,'Default partition существует и содержит out-of-range',
 $$SELECT (EXISTS(SELECT 1 FROM pg_partition_tree(
 'm_razhin.gps_16_default_partition'::regclass) p
 WHERE p.isleaf AND pg_partition_isdefault(p.relid))
 AND EXISTS(SELECT 1 FROM m_razhin.gps_16_default_partition
 WHERE event_date>=DATE '2030-01-01'))::text$$,
 $$SELECT true::text$$),
('storage_partitioning',17,2,'Новая partition принимает следующий месяц',
 $$SELECT (EXISTS(SELECT 1 FROM m_razhin.gps_17_add_partition
 WHERE event_date>=DATE '2025-04-01' AND event_date<DATE '2025-05-01'))::text$$,
 $$SELECT true::text$$),
('storage_partitioning',18,2,'Удаление partition зафиксировано',
 $$SELECT (partition_count_after<partition_count_before
 AND rows_after<rows_before)::text FROM m_razhin.gps_18_drop_partition$$,
 $$SELECT true::text$$),
('storage_partitioning',19,2,'Очищена только выбранная partition',
 $$SELECT (target_rows_after=0 AND other_rows_after=other_rows_before)::text
 FROM m_razhin.gps_19_truncate_partition$$,
 $$SELECT true::text$$),
('storage_partitioning',20,2,'Default split сохранил общее число строк',
 $$SELECT (rows_before=rows_after AND explicit_partition_rows>0)::text
 FROM m_razhin.gps_20_split_default$$,
 $$SELECT true::text$$),
('storage_partitioning',21,2,'Staging совместима по policy и числу колонок',
 $$SELECT (
 pg_get_table_distributedby('m_razhin.gps_21_staging_like'::regclass)
 =pg_get_table_distributedby('m_razhin.gps_11_range_partition'::regclass)
 AND (SELECT count(*) FROM pg_attribute WHERE attrelid=
 'm_razhin.gps_21_staging_like'::regclass AND attnum>0 AND NOT attisdropped)
 =(SELECT count(*) FROM pg_attribute WHERE attrelid=
 'm_razhin.gps_11_range_partition'::regclass AND attnum>0 AND NOT attisdropped)
 )::text$$,
 $$SELECT true::text$$),
('storage_partitioning',22,2,'Staging содержит только последнюю дату',
 $$SELECT (count(*)>0 AND min(event_date)=max(event_date)
 AND max(event_date)=(SELECT max(event_date) FROM greenplum_training.storage_source))::text
 FROM m_razhin.gps_22_stage_latest$$,
 $$SELECT true::text$$),
('storage_partitioning',23,2,'Ключ staging перенесён в следующий месяц',
 $$SELECT (count(*)>0 AND min(event_date)>=DATE '2025-04-01'
 AND max(event_date)<DATE '2025-05-01')::text
 FROM m_razhin.gps_23_change_key$$,
 $$SELECT true::text$$),
('storage_partitioning',24,2,'Target partition создана пустой',
 $$SELECT (target_exists AND target_rows=0)::text
 FROM m_razhin.gps_24_add_exchange_target$$,
 $$SELECT true::text$$),
('storage_partitioning',25,2,'Exchange разместил строки через parent',
 $$SELECT (exchanged_rows>0 AND staging_after_rows=0)::text
 FROM m_razhin.gps_25_exchange_without_validation$$,
 $$SELECT true::text$$),
('storage_partitioning',26,2,'Сверка exchange сошлась',
 $$SELECT (source_rows=target_rows AND difference_rows=0)::text
 FROM m_razhin.gps_26_exchange_counts$$,
 $$SELECT true::text$$),
('storage_partitioning',27,2,'Metadata exchange не переписал объём',
 $$SELECT (relfilenode_swapped AND size_before=size_after)::text
 FROM m_razhin.gps_27_exchange_metadata$$,
 $$SELECT true::text$$),
('storage_partitioning',28,2,'Создано два уровня и несколько leaf',
 $$SELECT ((SELECT max(level)>=2 FROM pg_partition_tree(
 'm_razhin.gps_28_multilevel'::regclass))
 AND (SELECT count(*)>=4 FROM pg_partition_tree(
 'm_razhin.gps_28_multilevel'::regclass) WHERE isleaf))::text$$,
 $$SELECT true::text$$),
('storage_partitioning',29,2,'Skew рассчитан для каждой leaf',
 $$SELECT (count(*)=(SELECT count(*) FROM pg_partition_tree(
 'm_razhin.gps_28_multilevel'::regclass) WHERE isleaf)
 AND min(skew_ratio)>=1)::text FROM m_razhin.gps_29_partition_skew$$,
 $$SELECT true::text$$),
('storage_partitioning',30,2,'Итог сравнивает минимум шесть вариантов',
 $$SELECT (count(*)>=6 AND bool_and(storage IS NOT NULL
 AND size_bytes>0 AND skew_ratio>=1 AND verdict IS NOT NULL))::text
 FROM m_razhin.gps_30_recommendation$$,
 $$SELECT true::text$$);
