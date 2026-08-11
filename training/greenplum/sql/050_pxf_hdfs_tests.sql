DELETE FROM greenplum_training.task_tests WHERE module_name='pxf_hdfs';
INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql)
SELECT 'pxf_hdfs',n,1,'Объект создан',
 format('SELECT greenplum_training.relation_exists(%L)::text',
 format('m_razhin.gpx_%s_%s',lpad(n::text,2,'0'),suffix)),
 'SELECT true::text'
FROM (VALUES
(1,'config'),(2,'metrica_ext'),(3,'metrica_count'),(4,'metrica_profile'),
(5,'projection'),(6,'predicate'),(7,'fragments'),(8,'file_layout'),
(9,'schema_map'),(10,'null_profile'),(11,'countries_write'),
(12,'countries_insert'),(13,'countries_read'),(14,'roundtrip'),
(15,'append'),(16,'partition_path'),(17,'multi_path'),(18,'path_column'),
(19,'small_files'),(20,'compaction'),(21,'moex_ext'),(22,'moex_filter'),
(23,'moex_projection'),(24,'type_mismatch'),(25,'missing_path'),
(26,'pxf_status'),(27,'external_vs_internal'),(28,'pushdown_report'),
(29,'reconciliation'),(30,'pipeline')) x(n,suffix);

INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql) VALUES
('pxf_hdfs',1,2,'Конфигурация соответствует стенду',
 $$SELECT (namenode_host='namenode' AND namenode_port=9000
 AND pxf_port=5888 AND hdfs_user='gpadmin')::text FROM m_razhin.gpx_01_config$$,$$SELECT true::text$$),
('pxf_hdfs',2,2,'Metadata указывает PXF Parquet',
 $$SELECT (source_schema='dds' AND source_table='ext_raw_yndx_metrica_logs'
 AND location ILIKE 'pxf://%' AND profile ILIKE '%parquet%')::text FROM m_razhin.gpx_02_metrica_ext$$,$$SELECT true::text$$),
('pxf_hdfs',3,2,'Метрика имеет строки и корректный диапазон',
 $$SELECT (row_count>0 AND min_date<=max_date)::text FROM m_razhin.gpx_03_metrica_count$$,$$SELECT true::text$$),
('pxf_hdfs',4,2,'Профиль Метрики заполнен',
 $$SELECT (total_rows>0 AND distinct_dates>0 AND distinct_countries>0
 AND distinct_cities>0 AND distinct_ips>0)::text FROM m_razhin.gpx_04_metrica_profile$$,$$SELECT true::text$$),
('pxf_hdfs',5,2,'Узкая проекция читает не больше широкой',
 $$SELECT (narrow_columns<wide_columns AND narrow_bytes<=wide_bytes)::text FROM m_razhin.gpx_05_projection$$,$$SELECT true::text$$),
('pxf_hdfs',6,2,'Predicate сокращает строки и отмечен в плане',
 $$SELECT (filtered_rows<=all_rows AND predicate_present)::text FROM m_razhin.gpx_06_predicate$$,$$SELECT true::text$$),
('pxf_hdfs',7,2,'Fragment profile учитывает все строки',
 $$SELECT (sum(rows_count)>0 AND count(*) BETWEEN 1 AND 4)::text FROM m_razhin.gpx_07_fragments$$,$$SELECT true::text$$),
('pxf_hdfs',8,2,'HDFS layout непуст',
 $$SELECT (file_count>0 AND partition_count>0 AND total_bytes>0)::text FROM m_razhin.gpx_08_file_layout$$,$$SELECT true::text$$),
('pxf_hdfs',9,2,'Schema map покрывает все external колонки',
 $$SELECT (count(*)=(SELECT count(*) FROM pg_attribute WHERE attrelid='dds.ext_raw_yndx_metrica_logs'::regclass
 AND attnum>0 AND NOT attisdropped) AND bool_and(gp_type IS NOT NULL AND parquet_type IS NOT NULL))::text FROM m_razhin.gpx_09_schema_map$$,$$SELECT true::text$$),
('pxf_hdfs',10,2,'NULL profile имеет обязательные колонки',
 $$SELECT (count(*)>=4 AND bool_and(column_name IS NOT NULL AND null_count>=0))::text FROM m_razhin.gpx_10_null_profile$$,$$SELECT true::text$$),
('pxf_hdfs',11,2,'Writable PXF использует персональный путь',
 $$SELECT (writable AND array_to_string(urilocation,',') LIKE '%pxf://data/raw/m_razhin/training/pxf/%'
 AND array_to_string(urilocation,',') ILIKE '%PROFILE=hdfs:parquet%')::text FROM pg_exttable WHERE reloid='m_razhin.gpx_11_countries_write'::regclass$$,$$SELECT true::text$$),
('pxf_hdfs',12,2,'Audit записи countries равен 173',
 $$SELECT (source_rows=173 AND written_rows=173 AND status='SUCCESS')::text FROM m_razhin.gpx_12_countries_insert$$,$$SELECT true::text$$),
('pxf_hdfs',13,2,'Readable PXF читает 173 страны',
 $$SELECT ((SELECT count(*) FROM m_razhin.gpx_13_countries_read)=173 AND EXISTS(
 SELECT 1 FROM pg_exttable WHERE reloid='m_razhin.gpx_13_countries_read'::regclass
 AND NOT writable AND array_to_string(urilocation,',') LIKE '%*%'))::text$$,$$SELECT true::text$$),
('pxf_hdfs',14,2,'Parquet round-trip совпал',
 $$SELECT (source_count=read_count AND source_count=173 AND checksum_equal)::text FROM m_razhin.gpx_14_roundtrip$$,$$SELECT true::text$$),
('pxf_hdfs',15,2,'Append увеличил число строк/файлов',
 $$SELECT (rows_after>rows_before AND files_after>=files_before)::text FROM m_razhin.gpx_15_append$$,$$SELECT true::text$$),
('pxf_hdfs',16,2,'Partition path содержит load_date',
 $$SELECT (location LIKE '%load_date=%' AND written_rows>0)::text FROM m_razhin.gpx_16_partition_path$$,$$SELECT true::text$$),
('pxf_hdfs',17,2,'Multi-path читает ожидаемые partitions',
 $$SELECT (partition_count>=2 AND row_count>0)::text FROM m_razhin.gpx_17_multi_path$$,$$SELECT true::text$$),
('pxf_hdfs',18,2,'Path value заполнен и согласован',
 $$SELECT (count(*)>0 AND count(*) FILTER(WHERE load_date IS NULL)=0)::text FROM m_razhin.gpx_18_path_column$$,$$SELECT true::text$$),
('pxf_hdfs',19,2,'Small-file метрики рассчитаны',
 $$SELECT (file_count>0 AND total_bytes>0 AND avg_file_bytes>0 AND small_file_count>=0)::text FROM m_razhin.gpx_19_small_files$$,$$SELECT true::text$$),
('pxf_hdfs',20,2,'Compaction сохраняет строки и уменьшает файлы',
 $$SELECT (rows_before=rows_after AND files_after<files_before AND checksum_equal)::text FROM m_razhin.gpx_20_compaction$$,$$SELECT true::text$$),
('pxf_hdfs',21,2,'MOEX metadata указывает Parquet path',
 $$SELECT (location LIKE '%moex_labs/raw/trades%' AND profile ILIKE '%parquet%')::text FROM m_razhin.gpx_21_moex_ext$$,$$SELECT true::text$$),
('pxf_hdfs',22,2,'MOEX filter ограничен одним ticker/day',
 $$SELECT (row_count>0 AND distinct_tickers=1 AND distinct_dates=1 AND fragment_count>0)::text FROM m_razhin.gpx_22_moex_filter$$,$$SELECT true::text$$),
('pxf_hdfs',23,2,'Узкая MOEX проекция дешевле/не дороже',
 $$SELECT (narrow_columns<wide_columns AND narrow_bytes<=wide_bytes)::text FROM m_razhin.gpx_23_moex_projection$$,$$SELECT true::text$$),
('pxf_hdfs',24,2,'Type mismatch диагностирован',
 $$SELECT (failed AND sqlstate IS NOT NULL AND error_message IS NOT NULL)::text FROM m_razhin.gpx_24_type_mismatch$$,$$SELECT true::text$$),
('pxf_hdfs',25,2,'Missing path диагностирован отдельно',
 $$SELECT (failed AND error_category='PATH_NOT_FOUND' AND pxf_reachable)::text FROM m_razhin.gpx_25_missing_path$$,$$SELECT true::text$$),
('pxf_hdfs',26,2,'PXF работает на обоих segment hosts',
 $$SELECT (count(*)=2 AND bool_and(status='RUNNING' AND port=5888))::text FROM m_razhin.gpx_26_pxf_status$$,$$SELECT true::text$$),
('pxf_hdfs',27,2,'External/internal сравниваются на равном результате',
 $$SELECT (external_count=internal_count AND checksum_equal AND external_ms>=0 AND internal_ms>=0)::text FROM m_razhin.gpx_27_external_vs_internal$$,$$SELECT true::text$$),
('pxf_hdfs',28,2,'Pushdown report содержит несколько запросов',
 $$SELECT (count(*)>=3 AND bool_and(query_name IS NOT NULL AND predicate_pushdown IS NOT NULL AND projection_columns>0))::text FROM m_razhin.gpx_28_pushdown_report$$,$$SELECT true::text$$),
('pxf_hdfs',29,2,'Manifest/external/internal согласованы',
 $$SELECT (manifest_files>0 AND manifest_bytes>0 AND external_rows=internal_rows AND checksum_equal)::text FROM m_razhin.gpx_29_reconciliation$$,$$SELECT true::text$$),
('pxf_hdfs',30,2,'PXF pipeline полный',
 $$SELECT (count(*)>=5 AND bool_and(stage_name IS NOT NULL AND status='SUCCESS'))::text FROM m_razhin.gpx_30_pipeline$$,$$SELECT true::text$$);
