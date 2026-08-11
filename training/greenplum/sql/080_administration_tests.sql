DROP TABLE IF EXISTS greenplum_training.admin_lab;
CREATE TABLE greenplum_training.admin_lab AS
SELECT event_id,country,payload FROM greenplum_training.dist_source
DISTRIBUTED BY(event_id);
UPDATE greenplum_training.admin_lab SET payload=payload||'_changed' WHERE event_id<=1000;
ANALYZE greenplum_training.admin_lab;

DELETE FROM greenplum_training.task_tests WHERE module_name='administration';
INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql)
SELECT 'administration',n,1,'Диагностический объект создан',
 format('SELECT greenplum_training.relation_exists(%L)::text',
 format('m_razhin.gpa_%s_%s',lpad(n::text,2,'0'),suffix)),
 'SELECT true::text'
FROM (VALUES
(1,'topology'),(2,'health'),(3,'role_drift'),(4,'host_balance'),
(5,'version'),(6,'sessions'),(7,'long_queries'),(8,'idle_tx'),
(9,'locks'),(10,'blockers'),(11,'schema_sizes'),(12,'table_sizes'),
(13,'segment_sizes'),(14,'skew'),(15,'bloat'),(16,'stats_age'),
(17,'analyze'),(18,'vacuum'),(19,'ao_stats'),(20,'partitions'),
(21,'resource_groups'),(22,'memory'),(23,'spill'),(24,'cancel'),
(25,'terminate'),(26,'pxf'),(27,'hdfs'),(28,'incident'),
(29,'runbook'),(30,'dashboard')) x(n,suffix);

INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql) VALUES
('administration',1,2,'Топология содержит 10 экземпляров',
 $$SELECT (count(*)=10 AND count(*) FILTER(WHERE content>=0 AND role='p')=4 AND count(*) FILTER(WHERE content>=0 AND role='m')=4 AND count(*) FILTER(WHERE content=-1)=2)::text FROM m_razhin.gpa_01_topology$$,$$SELECT true::text$$),
('administration',2,2,'Кластер полностью up/sync',
 $$SELECT (instances_up=instances_total AND instances_total=10 AND unsynchronized_instances=0)::text FROM m_razhin.gpa_02_health$$,$$SELECT true::text$$),
('administration',3,2,'Role drift измерен',
 $$SELECT (drift_count>=0 AND checked_instances=10)::text FROM m_razhin.gpa_03_role_drift$$,$$SELECT true::text$$),
('administration',4,2,'Host balance покрывает все узлы',
 $$SELECT (count(*)=4 AND sum(primary_count)=5 AND sum(mirror_count)=5)::text FROM m_razhin.gpa_04_host_balance$$,$$SELECT true::text$$),
('administration',5,2,'Версия и extensions зафиксированы',
 $$SELECT (server_version ILIKE '%Cloudberry%' AND pxf_installed AND gp_toolkit_installed)::text FROM m_razhin.gpa_05_version$$,$$SELECT true::text$$),
('administration',6,2,'Session view имеет безопасные поля',
 $$SELECT (count(*)>=1 AND bool_and(pid IS NOT NULL AND usename IS NOT NULL AND state IS NOT NULL))::text FROM m_razhin.gpa_06_sessions$$,$$SELECT true::text$$),
('administration',7,2,'Long query age неотрицателен',
 $$SELECT coalesce(bool_and(duration_seconds>=0),true)::text FROM m_razhin.gpa_07_long_queries$$,$$SELECT true::text$$),
('administration',8,2,'Idle transaction age неотрицателен',
 $$SELECT coalesce(bool_and(transaction_age_seconds>=0 AND state='idle in transaction'),true)::text FROM m_razhin.gpa_08_idle_tx$$,$$SELECT true::text$$),
('administration',9,2,'Lock waits имеют PID и тип',
 $$SELECT coalesce(bool_and(pid IS NOT NULL AND locktype IS NOT NULL AND NOT granted),true)::text FROM m_razhin.gpa_09_locks$$,$$SELECT true::text$$),
('administration',10,2,'Blocker mapping не содержит self-loop',
 $$SELECT coalesce(bool_and(blocked_pid<>blocker_pid),true)::text FROM m_razhin.gpa_10_blockers$$,$$SELECT true::text$$),
('administration',11,2,'Размеры схем положительны',
 $$SELECT (count(*)>=2 AND min(size_bytes)>=0)::text FROM m_razhin.gpa_11_schema_sizes$$,$$SELECT true::text$$),
('administration',12,2,'Таблицы имеют storage/policy/size',
 $$SELECT (count(*)>=5 AND bool_and(table_name IS NOT NULL AND size_bytes>0 AND storage IS NOT NULL AND policy IS NOT NULL))::text FROM m_razhin.gpa_12_table_sizes$$,$$SELECT true::text$$),
('administration',13,2,'Размер выбранной таблицы на 4 сегментах',
 $$SELECT (count(*)=4 AND sum(size_bytes)>0)::text FROM m_razhin.gpa_13_segment_sizes$$,$$SELECT true::text$$),
('administration',14,2,'Skew metrics нормированы',
 $$SELECT (count(*)>=3 AND bool_and(row_skew_ratio>=1 AND byte_skew_ratio>=1))::text FROM m_razhin.gpa_14_skew$$,$$SELECT true::text$$),
('administration',15,2,'Bloat оценка имеет метод и границы',
 $$SELECT (estimated_bloat_bytes>=0 AND bloat_ratio>=0 AND method IS NOT NULL)::text FROM m_razhin.gpa_15_bloat$$,$$SELECT true::text$$),
('administration',16,2,'Stats gaps измерены',
 $$SELECT (count(*)>=1 AND bool_and(table_name IS NOT NULL AND stats_status IS NOT NULL))::text FROM m_razhin.gpa_16_stats_age$$,$$SELECT true::text$$),
('administration',17,2,'ANALYZE создал статистику и улучшил/сохранил оценку',
 $$SELECT (stats_rows_after>0 AND error_ratio_after<=error_ratio_before)::text FROM m_razhin.gpa_17_analyze$$,$$SELECT true::text$$),
('administration',18,2,'VACUUM ограничен admin_lab',
 $$SELECT (table_name='greenplum_training.admin_lab' AND completed AND dead_tuples_after<=dead_tuples_before)::text FROM m_razhin.gpa_18_vacuum$$,$$SELECT true::text$$),
('administration',19,2,'AO metadata покрывает AO таблицы',
 $$SELECT (count(*)>=1 AND bool_and(table_name IS NOT NULL AND orientation IS NOT NULL AND compression IS NOT NULL))::text FROM m_razhin.gpa_19_ao_stats$$,$$SELECT true::text$$),
('administration',20,2,'Partition report имеет thresholds',
 $$SELECT (partitioned_tables>=0 AND leaf_partitions>=0 AND small_partitions>=0 AND threshold_bytes>0)::text FROM m_razhin.gpa_20_partitions$$,$$SELECT true::text$$),
('administration',21,2,'Resource groups имеют limits',
 $$SELECT (count(*)>=1 AND bool_and(group_name IS NOT NULL AND concurrency_limit>=0))::text FROM m_razhin.gpa_21_resource_groups$$,$$SELECT true::text$$),
('administration',22,2,'Memory context заполнен',
 $$SELECT (statement_mem IS NOT NULL AND resource_group IS NOT NULL AND session_user IS NOT NULL)::text FROM m_razhin.gpa_22_memory$$,$$SELECT true::text$$),
('administration',23,2,'Spill metrics неотрицательны',
 $$SELECT (spill_files>=0 AND spill_bytes>=0 AND spill_queries>=0)::text FROM m_razhin.gpa_23_spill$$,$$SELECT true::text$$),
('administration',24,2,'Cancel ограничен собственной учебной сессией',
 $$SELECT (target_pid IS NOT NULL AND target_user=current_user AND cancel_result AND target_label='greenplum_training_cancel_lab')::text FROM m_razhin.gpa_24_cancel$$,$$SELECT true::text$$),
('administration',25,2,'Cancel/terminate различие описано',
 $$SELECT (cancel_keeps_session AND terminate_closes_session AND rollback_on_terminate)::text FROM m_razhin.gpa_25_terminate$$,$$SELECT true::text$$),
('administration',26,2,'PXF ready на двух hosts',
 $$SELECT (count(*)=2 AND bool_and(extension_installed AND server_status='RUNNING' AND port=5888))::text FROM m_razhin.gpa_26_pxf$$,$$SELECT true::text$$),
('administration',27,2,'HDFS ready и персональный path доступен',
 $$SELECT (namenode_ready AND datanodes_ready>=2 AND personal_path_exists AND personal_path_writable)::text FROM m_razhin.gpa_27_hdfs$$,$$SELECT true::text$$),
('administration',28,2,'Incident report содержит evidence',
 $$SELECT (query_id IS NOT NULL AND plan_checked AND skew_checked AND motion_checked AND spill_checked AND locks_checked AND stats_checked AND conclusion IS NOT NULL)::text FROM m_razhin.gpa_28_incident$$,$$SELECT true::text$$),
('administration',29,2,'Runbook покрывает типовые симптомы',
 $$SELECT (count(*)>=6 AND bool_and(symptom IS NOT NULL AND diagnostic_query IS NOT NULL AND safe_action IS NOT NULL AND escalation_condition IS NOT NULL))::text FROM m_razhin.gpa_29_runbook$$,$$SELECT true::text$$),
('administration',30,2,'Dashboard покрывает все подсистемы',
 $$SELECT (count(DISTINCT subsystem)>=6 AND bool_and(metric_name IS NOT NULL AND status IN('OK','WARN','CRITICAL') AND checked_at IS NOT NULL))::text FROM m_razhin.gpa_30_dashboard$$,$$SELECT true::text$$);
