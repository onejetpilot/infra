DROP TABLE IF EXISTS greenplum_training.etl_source;
CREATE TABLE greenplum_training.etl_source AS
SELECT event_id,event_date,user_id,country,city,payload,
       event_date::timestamp + (event_id%86400)*interval '1 second' updated_at,
       1 version,false is_deleted
FROM greenplum_training.dist_source
UNION ALL
SELECT event_id,event_date,user_id,country,city,payload||'_v2',
       event_date::timestamp+interval '2 days',2,false
FROM greenplum_training.dist_source WHERE event_id<=100
UNION ALL
SELECT event_id,event_date,user_id,country,city,payload,
       event_date::timestamp+interval '3 days',3,true
FROM greenplum_training.dist_source WHERE event_id BETWEEN 91 AND 100
DISTRIBUTED BY(event_id);
ANALYZE greenplum_training.etl_source;

DELETE FROM greenplum_training.task_tests WHERE module_name='etl';
INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql)
SELECT 'etl',n,1,'Объект создан',
 format('SELECT greenplum_training.relation_exists(%L)::text',
 format('m_razhin.gpe_%s_%s',lpad(n::text,2,'0'),suffix)),
 'SELECT true::text'
FROM (VALUES
(1,'layers'),(2,'batch_control'),(3,'start_batch'),(4,'raw_snapshot'),
(5,'raw_reconcile'),(6,'staging_cast'),(7,'quality_rules'),(8,'rejects'),
(9,'full_refresh'),(10,'full_idempotent'),(11,'watermark'),(12,'increment'),
(13,'increment_load'),(14,'advance_watermark'),(15,'rerun_increment'),
(16,'late_arrival'),(17,'upsert_pattern'),(18,'changed_rows'),
(19,'delete_insert'),(20,'partition_reload'),(21,'deduplicate'),
(22,'delete_events'),(23,'scd1'),(24,'scd2'),(25,'fact_lookup'),
(26,'reconciliation'),(27,'failure'),(28,'retry'),(29,'sla'),(30,'pipeline')) x(n,suffix);

INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql) VALUES
('etl',1,2,'Карта содержит четыре слоя',
 $$SELECT (count(DISTINCT layer_name)=4 AND bool_and(grain IS NOT NULL AND responsibility IS NOT NULL))::text FROM m_razhin.gpe_01_layers$$,$$SELECT true::text$$),
('etl',2,2,'Batch control имеет обязательные поля',
 $$SELECT (count(*)>=0 AND EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='m_razhin' AND table_name='gpe_02_batch_control' AND column_name='batch_id') AND EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='m_razhin' AND table_name='gpe_02_batch_control' AND column_name='status'))::text FROM m_razhin.gpe_02_batch_control$$,$$SELECT true::text$$),
('etl',3,2,'Batch начат в RUNNING',
 $$SELECT (status='RUNNING' AND started_at IS NOT NULL AND finished_at IS NULL)::text FROM m_razhin.gpe_03_start_batch ORDER BY started_at DESC LIMIT 1$$,$$SELECT true::text$$),
('etl',4,2,'Raw snapshot содержит source и техполя',
 $$SELECT (count(*)=100110 AND count(*) FILTER(WHERE batch_id IS NULL OR load_dttm IS NULL)=0)::text FROM m_razhin.gpe_04_raw_snapshot$$,$$SELECT true::text$$),
('etl',5,2,'Raw reconciliation сошлась',
 $$SELECT (source_rows=raw_rows AND checksum_equal)::text FROM m_razhin.gpe_05_raw_reconcile$$,$$SELECT true::text$$),
('etl',6,2,'Typed staging имеет принятые строки',
 $$SELECT (accepted_rows>0 AND accepted_rows+rejected_rows=source_rows)::text FROM m_razhin.gpe_06_staging_cast$$,$$SELECT true::text$$),
('etl',7,2,'Quality catalog содержит несколько severity',
 $$SELECT (count(*)>=4 AND count(DISTINCT severity)>=2 AND bool_and(status IS NOT NULL))::text FROM m_razhin.gpe_07_quality_rules$$,$$SELECT true::text$$),
('etl',8,2,'Rejects имеют причину и batch',
 $$SELECT (count(*)>=0 AND count(*) FILTER(WHERE reason IS NULL OR batch_id IS NULL)=0)::text FROM m_razhin.gpe_08_rejects$$,$$SELECT true::text$$),
('etl',9,2,'Full target содержит канонические активные ключи',
 $$SELECT (count(*)=99990 AND count(*)=count(DISTINCT event_id))::text FROM m_razhin.gpe_09_full_refresh$$,$$SELECT true::text$$),
('etl',10,2,'Full refresh идемпотентен',
 $$SELECT (first_count=second_count AND first_checksum=second_checksum)::text FROM m_razhin.gpe_10_full_idempotent$$,$$SELECT true::text$$),
('etl',11,2,'Watermark составной и заполнен',
 $$SELECT (last_updated_at IS NOT NULL AND last_event_id IS NOT NULL)::text FROM m_razhin.gpe_11_watermark$$,$$SELECT true::text$$),
('etl',12,2,'Increment строго после watermark',
 $$SELECT (count(*)>=0 AND bool_and((updated_at,event_id)>(watermark_updated_at,watermark_event_id)))::text FROM m_razhin.gpe_12_increment$$,$$SELECT true::text$$),
('etl',13,2,'Increment target уникален',
 $$SELECT (count(*)=count(DISTINCT event_id))::text FROM m_razhin.gpe_13_increment_load$$,$$SELECT true::text$$),
('etl',14,2,'Watermark продвинут после success',
 $$SELECT (target_status='SUCCESS' AND new_watermark>=old_watermark)::text FROM m_razhin.gpe_14_advance_watermark$$,$$SELECT true::text$$),
('etl',15,2,'Rerun не создал дублей',
 $$SELECT (first_count=second_count AND duplicate_keys=0 AND checksum_equal)::text FROM m_razhin.gpe_15_rerun_increment$$,$$SELECT true::text$$),
('etl',16,2,'Late event принят ровно один раз',
 $$SELECT (late_detected AND target_occurrences=1)::text FROM m_razhin.gpe_16_late_arrival$$,$$SELECT true::text$$),
('etl',17,2,'Upsert сохранил уникальность и применил change',
 $$SELECT (changed_rows>0 AND duplicate_keys=0 AND unchanged_checksum_equal)::text FROM m_razhin.gpe_17_upsert_pattern$$,$$SELECT true::text$$),
('etl',18,2,'Hashdiff выделяет изменённые строки',
 $$SELECT (changed_rows=100 AND unchanged_rows>0 AND hash_algorithm IS NOT NULL)::text FROM m_razhin.gpe_18_changed_rows$$,$$SELECT true::text$$),
('etl',19,2,'Delete+insert ограничен одной датой',
 $$SELECT (distinct_reloaded_dates=1 AND before_rows=after_rows AND duplicate_keys=0)::text FROM m_razhin.gpe_19_delete_insert$$,$$SELECT true::text$$),
('etl',20,2,'Partition reload сохранил slice',
 $$SELECT (source_rows=target_rows AND checksum_equal AND exchanged)::text FROM m_razhin.gpe_20_partition_reload$$,$$SELECT true::text$$),
('etl',21,2,'Dedup выбирает последнюю версию',
 $$SELECT (count(*)=100000 AND count(*)=count(DISTINCT event_id) AND bool_and(version=expected_max_version))::text FROM m_razhin.gpe_21_deduplicate$$,$$SELECT true::text$$),
('etl',22,2,'Tombstones обработаны',
 $$SELECT (tombstones=10 AND active_target_rows=99990 AND deleted_keys_in_target=0)::text FROM m_razhin.gpe_22_delete_events$$,$$SELECT true::text$$),
('etl',23,2,'SCD1 имеет одну строку на ключ',
 $$SELECT (count(*)=count(DISTINCT business_key) AND changed_value_applied)::text FROM m_razhin.gpe_23_scd1$$,$$SELECT true::text$$),
('etl',24,2,'SCD2 интервалы корректны',
 $$SELECT (overlap_count=0 AND multiple_current_keys=0 AND invalid_intervals=0 AND history_keys>0)::text FROM m_razhin.gpe_24_scd2$$,$$SELECT true::text$$),
('etl',25,2,'Все факты нашли временную версию',
 $$SELECT (fact_rows>0 AND matched_rows=fact_rows AND ambiguous_matches=0)::text FROM m_razhin.gpe_25_fact_lookup$$,$$SELECT true::text$$),
('etl',26,2,'ETL reconciliation сошлась',
 $$SELECT (source_rows=accepted_rows+rejected_rows AND target_delta=expected_delta AND checksum_equal)::text FROM m_razhin.gpe_26_reconciliation$$,$$SELECT true::text$$),
('etl',27,2,'Failure не продвинул target/watermark',
 $$SELECT (status='FAILED' AND error_message IS NOT NULL AND target_unchanged AND watermark_unchanged)::text FROM m_razhin.gpe_27_failure$$,$$SELECT true::text$$),
('etl',28,2,'Retry завершён без дублей',
 $$SELECT (attempts>=2 AND final_status='SUCCESS' AND duplicate_keys=0 AND reconciliation_ok)::text FROM m_razhin.gpe_28_retry$$,$$SELECT true::text$$),
('etl',29,2,'SLA метрики рассчитаны',
 $$SELECT (duration_seconds>=0 AND rows_processed>=0 AND throughput_rows_sec>=0 AND sla_status IS NOT NULL)::text FROM m_razhin.gpe_29_sla$$,$$SELECT true::text$$),
('etl',30,2,'Pipeline audit полный',
 $$SELECT (count(*)>=8 AND bool_and(stage_name IS NOT NULL AND status='SUCCESS' AND started_at IS NOT NULL AND finished_at IS NOT NULL))::text FROM m_razhin.gpe_30_pipeline$$,$$SELECT true::text$$);
