DELETE FROM greenplum_training.task_tests WHERE module_name='gpfdist';
INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql)
SELECT 'gpfdist',n,1,'Объект создан',
 format('SELECT greenplum_training.relation_exists(%L)::text',
 format('m_razhin.gpg_%s_%s',lpad(n::text,2,'0'),suffix)),
 'SELECT true::text'
FROM (VALUES
(1,'endpoint'),(2,'countries_ext'),(3,'source_count'),(4,'source_profile'),
(5,'countries_heap'),(6,'countries_ao'),(7,'countries_repl'),(8,'trim'),
(9,'constraints'),(10,'reconciliation'),(11,'header_ext'),
(12,'delimiter_ext'),(13,'quote_escape'),(14,'null_mapping'),
(15,'encoding'),(16,'bad_rows'),(17,'reject_limit'),(18,'error_log'),
(19,'reject_threshold'),(20,'type_conversion'),(21,'multi_location'),
(22,'parallel_profile'),(23,'distribution_target'),(24,'writable_ext'),
(25,'export'),(26,'export_readback'),(27,'roundtrip'),
(28,'idempotent_load'),(29,'audit'),(30,'pipeline')) x(n,suffix);

INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql) VALUES
('gpfdist',1,2,'Endpoint соответствует инфраструктуре',
 $$SELECT (host='cdw' AND port=8080 AND path='/countries.csv')::text FROM m_razhin.gpg_01_endpoint$$,$$SELECT true::text$$),
('gpfdist',2,2,'External использует GPFDIST и читает 173 строки',
 $$SELECT ((SELECT count(*) FROM m_razhin.gpg_02_countries_ext)=173 AND
 EXISTS(SELECT 1 FROM pg_exttable WHERE reloid='m_razhin.gpg_02_countries_ext'::regclass
 AND array_to_string(urilocation,',') LIKE '%gpfdist://cdw:8080/countries.csv%'))::text$$,$$SELECT true::text$$),
('gpfdist',3,2,'Source count зафиксирован',
 $$SELECT (source_rows=173)::text FROM m_razhin.gpg_03_source_count$$,$$SELECT true::text$$),
('gpfdist',4,2,'Профиль источника полный',
 $$SELECT (total_rows=173 AND distinct_codes=173 AND null_codes=0)::text FROM m_razhin.gpg_04_source_profile$$,$$SELECT true::text$$),
('gpfdist',5,2,'Heap target загружена',
 $$SELECT ((SELECT count(*) FROM m_razhin.gpg_05_countries_heap)=173 AND NOT EXISTS(
 SELECT 1 FROM pg_appendonly WHERE relid='m_razhin.gpg_05_countries_heap'::regclass))::text$$,$$SELECT true::text$$),
('gpfdist',6,2,'AO column target загружена',
 $$SELECT (columnstore AND compresstype='zstd' AND
 (SELECT count(*) FROM m_razhin.gpg_06_countries_ao)=173)::text
 FROM pg_appendonly WHERE relid='m_razhin.gpg_06_countries_ao'::regclass$$,$$SELECT true::text$$),
('gpfdist',7,2,'Справочник replicated',
 $$SELECT (pg_get_table_distributedby('m_razhin.gpg_07_countries_repl'::regclass)='DISTRIBUTED REPLICATED'
 AND (SELECT count(*) FROM m_razhin.gpg_07_countries_repl)=173)::text$$,$$SELECT true::text$$),
('gpfdist',8,2,'Очистка не потеряла строки',
 $$SELECT (count(*)=173 AND bool_and(country_code=trim(country_code)
 AND country_name=trim(country_name)))::text FROM m_razhin.gpg_08_trim$$,$$SELECT true::text$$),
('gpfdist',9,2,'Quality проверки выполнены',
 $$SELECT (duplicate_codes=0 AND invalid_codes=0 AND null_names=0)::text FROM m_razhin.gpg_09_constraints$$,$$SELECT true::text$$),
('gpfdist',10,2,'Reconciliation сошлась',
 $$SELECT (source_count=target_count AND checksum_equal AND rejected_count=0)::text FROM m_razhin.gpg_10_reconciliation$$,$$SELECT true::text$$),
('gpfdist',11,2,'HEADER пропущен',
 $$SELECT ((SELECT count(*) FROM m_razhin.gpg_11_header_ext)=3 AND
 EXISTS(SELECT 1 FROM pg_exttable WHERE reloid='m_razhin.gpg_11_header_ext'::regclass AND fmtopts ILIKE '%header%'))::text$$,$$SELECT true::text$$),
('gpfdist',12,2,'Pipe delimiter разобран',
 $$SELECT ((SELECT count(*) FROM m_razhin.gpg_12_delimiter_ext)=3 AND
 EXISTS(SELECT 1 FROM pg_exttable WHERE reloid='m_razhin.gpg_12_delimiter_ext'::regclass AND fmtopts LIKE '%|%'))::text$$,$$SELECT true::text$$),
('gpfdist',13,2,'Quoted delimiter сохранён внутри значения',
 $$SELECT (count(*)=2 AND bool_or(country_name LIKE '%,%'))::text FROM m_razhin.gpg_13_quote_escape$$,$$SELECT true::text$$),
('gpfdist',14,2,'NULL marker отличается от пустой строки',
 $$SELECT (count(*)=3 AND count(*) FILTER(WHERE country_name IS NULL)=1
 AND count(*) FILTER(WHERE country_name='')=1)::text FROM m_razhin.gpg_14_null_mapping$$,$$SELECT true::text$$),
('gpfdist',15,2,'Encoding зафиксирован',
 $$SELECT (encoding_name ILIKE 'UTF%')::text FROM m_razhin.gpg_15_encoding$$,$$SELECT true::text$$),
('gpfdist',16,2,'Bad source содержит пять raw строк',
 $$SELECT (count(*)=5)::text FROM m_razhin.gpg_16_bad_rows$$,$$SELECT true::text$$),
('gpfdist',17,2,'Reject policy настроена',
 $$SELECT (rejectlimit>0 AND logerrors)::text FROM pg_exttable WHERE reloid='m_razhin.gpg_17_reject_limit'::regclass$$,$$SELECT true::text$$),
('gpfdist',18,2,'Rejected rows диагностированы',
 $$SELECT (rejected_rows=2 AND accepted_rows=3 AND last_error IS NOT NULL)::text FROM m_razhin.gpg_18_error_log$$,$$SELECT true::text$$),
('gpfdist',19,2,'Превышение порога зафиксировано',
 $$SELECT (threshold_exceeded AND sqlstate IS NOT NULL)::text FROM m_razhin.gpg_19_reject_threshold$$,$$SELECT true::text$$),
('gpfdist',20,2,'Typed staging содержит допустимые строки',
 $$SELECT (count(*)=3 AND min(id)=1 AND max(id)=4)::text FROM m_razhin.gpg_20_type_conversion$$,$$SELECT true::text$$),
('gpfdist',21,2,'Используется несколько URI',
 $$SELECT (cardinality(urilocation)>=2 AND (SELECT count(*) FROM m_razhin.gpg_21_multi_location)=4)::text FROM pg_exttable WHERE reloid='m_razhin.gpg_21_multi_location'::regclass$$,$$SELECT true::text$$),
('gpfdist',22,2,'Сегментный профиль покрывает источник',
 $$SELECT (sum(rows_count)=173 AND count(*)>=1)::text FROM m_razhin.gpg_22_parallel_profile$$,$$SELECT true::text$$),
('gpfdist',23,2,'Target policy явно выбрана',
 $$SELECT (policy IS NOT NULL AND policy<>'DISTRIBUTED RANDOMLY' AND target_rows=173)::text FROM m_razhin.gpg_23_distribution_target$$,$$SELECT true::text$$),
('gpfdist',24,2,'External является writable GPFDIST',
 $$SELECT (writable AND array_to_string(urilocation,',') LIKE '%gpfdist://%')::text FROM pg_exttable WHERE reloid='m_razhin.gpg_24_writable_ext'::regclass$$,$$SELECT true::text$$),
('gpfdist',25,2,'Экспорт записал строки',
 $$SELECT (exported_rows>0 AND output_files>0)::text FROM m_razhin.gpg_25_export$$,$$SELECT true::text$$),
('gpfdist',26,2,'Readback доступен',
 $$SELECT (count(*)>0)::text FROM m_razhin.gpg_26_export_readback$$,$$SELECT true::text$$),
('gpfdist',27,2,'Roundtrip содержательно равен',
 $$SELECT (source_count=readback_count AND checksum_equal)::text FROM m_razhin.gpg_27_roundtrip$$,$$SELECT true::text$$),
('gpfdist',28,2,'Повторная загрузка не создаёт дубли',
 $$SELECT (first_run_count=second_run_count AND duplicate_codes=0)::text FROM m_razhin.gpg_28_idempotent_load$$,$$SELECT true::text$$),
('gpfdist',29,2,'Audit согласован',
 $$SELECT (source_rows=target_rows+rejected_rows AND status='SUCCESS')::text FROM m_razhin.gpg_29_audit$$,$$SELECT true::text$$),
('gpfdist',30,2,'Pipeline содержит все этапы',
 $$SELECT (count(*)>=5 AND bool_and(stage_name IS NOT NULL AND status IS NOT NULL))::text FROM m_razhin.gpg_30_pipeline$$,$$SELECT true::text$$);
