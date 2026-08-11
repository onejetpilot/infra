DROP TABLE IF EXISTS greenplum_training.opt_fact;
CREATE TABLE greenplum_training.opt_fact
WITH (appendoptimized=true, orientation=column, compresstype=zstd, compresslevel=1)
AS SELECT * FROM greenplum_training.dist_source
DISTRIBUTED BY (event_id);

DROP TABLE IF EXISTS greenplum_training.opt_dim;
CREATE TABLE greenplum_training.opt_dim AS
SELECT * FROM greenplum_training.dist_dimension
DISTRIBUTED BY (country);
ANALYZE greenplum_training.opt_fact;
ANALYZE greenplum_training.opt_dim;

CREATE OR REPLACE FUNCTION greenplum_training.explain_lines(p_query text)
RETURNS TABLE(line_no integer, plan_line text)
LANGUAGE plpgsql VOLATILE AS $$
DECLARE line text; n integer := 0;
BEGIN
  FOR line IN EXECUTE 'EXPLAIN '||p_query LOOP
    n:=n+1; RETURN QUERY SELECT n,line;
  END LOOP;
END $$;

DELETE FROM greenplum_training.task_tests WHERE module_name='query_optimization';
INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql)
SELECT 'query_optimization',n,1,'Объект результата создан',
 format('SELECT greenplum_training.relation_exists(%L)::text',
 format('m_razhin.gpo_%s_%s',lpad(n::text,2,'0'),suffix)),
 'SELECT true::text'
FROM (VALUES
(1,'explain'),(2,'analyze'),(3,'error_ratio'),(4,'no_stats'),
(5,'with_stats'),(6,'column_stats'),(7,'stats_target'),(8,'seq_scan'),
(9,'projection'),(10,'filter_pushdown'),(11,'hash_join'),
(12,'nested_loop'),(13,'bad_nested_loop'),(14,'broadcast'),
(15,'redistribute'),(16,'colocated'),(17,'join_order'),
(18,'semi_join'),(19,'anti_join'),(20,'skew_join'),
(21,'two_stage_agg'),(22,'group_key'),(23,'distinct'),(24,'sort'),
(25,'top_n'),(26,'spill'),(27,'no_spill'),(28,'partition_plan'),
(29,'metrica_query'),(30,'report')) x(n,suffix);

INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql) VALUES
('query_optimization',1,2,'План содержит scan node',
 $$SELECT bool_or(plan_line LIKE '%Scan%')::text FROM m_razhin.gpo_01_explain$$,
 $$SELECT true::text$$),
('query_optimization',2,2,'Сохранены estimated и actual rows',
 $$SELECT (estimated_rows>=0 AND actual_rows>=0)::text FROM m_razhin.gpo_02_analyze$$,
 $$SELECT true::text$$),
('query_optimization',3,2,'Cardinality ratio корректен',
 $$SELECT (error_ratio>=1 AND abs(error_ratio-
 CASE WHEN actual_rows=0 OR estimated_rows=0 THEN error_ratio
 ELSE greatest(estimated_rows/actual_rows,actual_rows/estimated_rows) END)<0.001)::text
 FROM m_razhin.gpo_03_error_ratio$$,
 $$SELECT true::text$$),
('query_optimization',4,2,'Копия действительно без пользовательской статистики',
 $$SELECT (NOT EXISTS(SELECT 1 FROM pg_stats
 WHERE schemaname='m_razhin' AND tablename='gpo_04_no_stats'))::text$$,
 $$SELECT true::text$$),
('query_optimization',5,2,'После ANALYZE статистика существует',
 $$SELECT EXISTS(SELECT 1 FROM pg_stats
 WHERE schemaname='m_razhin' AND tablename='gpo_05_with_stats')::text$$,
 $$SELECT true::text$$),
('query_optimization',6,2,'Профиль содержит две колонки',
 $$SELECT (count(*)=2 AND count(DISTINCT column_name)=2
 AND bool_and(n_distinct IS NOT NULL))::text FROM m_razhin.gpo_06_column_stats$$,
 $$SELECT true::text$$),
('query_optimization',7,2,'Statistics target повышен',
 $$SELECT (statistics_target>100 AND mcv_count>0)::text
 FROM m_razhin.gpo_07_stats_target$$,
 $$SELECT true::text$$),
('query_optimization',8,2,'Зафиксирован scan type',
 $$SELECT (scan_type ILIKE '%scan%' AND estimated_rows>0)::text
 FROM m_razhin.gpo_08_seq_scan$$,
 $$SELECT true::text$$),
('query_optimization',9,2,'Проекция читает не больше полного набора',
 $$SELECT (projected_columns<all_columns AND projected_bytes<=all_bytes)::text
 FROM m_razhin.gpo_09_projection$$,
 $$SELECT true::text$$),
('query_optimization',10,2,'Фильтр сокращает строки до Motion',
 $$SELECT (rows_after_filter<=rows_before_filter
 AND rows_motion<=rows_before_filter)::text FROM m_razhin.gpo_10_filter_pushdown$$,
 $$SELECT true::text$$);

INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql) VALUES
('query_optimization',11,2,'Зафиксирован Hash Join',
 $$SELECT (join_type ILIKE '%hash%join%' AND actual_rows>0)::text
 FROM m_razhin.gpo_11_hash_join$$, $$SELECT true::text$$),
('query_optimization',12,2,'Nested Loop работает на малом outer',
 $$SELECT (join_type ILIKE '%nested%loop%' AND outer_rows<=100
 AND result_rows>=0)::text FROM m_razhin.gpo_12_nested_loop$$,
 $$SELECT true::text$$),
('query_optimization',13,2,'Переписывание сохраняет результат и снижает работу',
 $$SELECT (rows_before=rows_after AND work_after<work_before)::text
 FROM m_razhin.gpo_13_bad_nested_loop$$, $$SELECT true::text$$),
('query_optimization',14,2,'Broadcast маленького измерения измерен',
 $$SELECT (motion_type ILIKE '%broadcast%' AND motion_rows<=100)::text
 FROM m_razhin.gpo_14_broadcast$$, $$SELECT true::text$$),
('query_optimization',15,2,'Redistribute измерен',
 $$SELECT (motion_type ILIKE '%redistribute%' AND motion_rows>0)::text
 FROM m_razhin.gpo_15_redistribute$$, $$SELECT true::text$$),
('query_optimization',16,2,'Colocated вариант сохраняет результат и уменьшает Motion',
 $$SELECT (rows_before=rows_after AND motion_after<motion_before)::text
 FROM m_razhin.gpo_16_colocated$$, $$SELECT true::text$$),
('query_optimization',17,2,'Порядки JOIN сравниваются по одинаковому результату',
 $$SELECT (result_rows_a=result_rows_b AND plan_cost_a>0 AND plan_cost_b>0)::text
 FROM m_razhin.gpo_17_join_order$$, $$SELECT true::text$$),
('query_optimization',18,2,'Semi join не размножает левую сторону',
 $$SELECT (exists_rows=join_distinct_rows AND exists_rows<=left_rows)::text
 FROM m_razhin.gpo_18_semi_join$$, $$SELECT true::text$$),
('query_optimization',19,2,'Anti join совпадает с эталонным отсутствием',
 $$SELECT (anti_rows=expected_rows AND has_null_safe_semantics)::text
 FROM m_razhin.gpo_19_anti_join$$, $$SELECT true::text$$),
('query_optimization',20,2,'Skew JOIN измерен на четырёх сегментах',
 $$SELECT (segment_count=4 AND max_rows>=avg_rows AND skew_ratio>=1)::text
 FROM m_razhin.gpo_20_skew_join$$, $$SELECT true::text$$),
('query_optimization',21,2,'Найдены partial и final aggregate',
 $$SELECT (partial_aggregate_count>=1 AND final_aggregate_count>=1)::text
 FROM m_razhin.gpo_21_two_stage_agg$$, $$SELECT true::text$$),
('query_optimization',22,2,'GROUP BY distribution key не дороже чужого',
 $$SELECT (local_motion_count<=foreign_motion_count
 AND local_rows=foreign_rows)::text FROM m_razhin.gpo_22_group_key$$,
 $$SELECT true::text$$),
('query_optimization',23,2,'Distinct даёт корректную кардинальность',
 $$SELECT (distinct_result=(SELECT count(DISTINCT user_id)
 FROM greenplum_training.opt_fact) AND motion_count>=0)::text
 FROM m_razhin.gpo_23_distinct$$, $$SELECT true::text$$),
('query_optimization',24,2,'Полная сортировка измеряет память или диск',
 $$SELECT (input_rows=100000 AND sort_method IS NOT NULL
 AND memory_kb>=0 AND disk_kb>=0)::text FROM m_razhin.gpo_24_sort$$,
 $$SELECT true::text$$),
('query_optimization',25,2,'Top-N сохраняет N строк и уменьшает работу',
 $$SELECT (result_rows=limit_rows AND work_after<work_before)::text
 FROM m_razhin.gpo_25_top_n$$, $$SELECT true::text$$),
('query_optimization',26,2,'Spill воспроизведён',
 $$SELECT (spill_bytes>0 AND statement_mem_kb>0)::text
 FROM m_razhin.gpo_26_spill$$, $$SELECT true::text$$),
('query_optimization',27,2,'Spill устранён с тем же результатом',
 $$SELECT (result_checksum_before=result_checksum_after
 AND spill_after_bytes<spill_before_bytes)::text
 FROM m_razhin.gpo_27_no_spill$$, $$SELECT true::text$$),
('query_optimization',28,2,'Pruning сокращает leaf scans',
 $$SELECT (partitions_with_pruning<partitions_without_pruning
 AND result_rows_equal)::text FROM m_razhin.gpo_28_partition_plan$$,
 $$SELECT true::text$$),
('query_optimization',29,2,'Оптимизация Метрики сохраняет результат',
 $$SELECT (result_checksum_before=result_checksum_after
 AND elapsed_after_ms<=elapsed_before_ms
 AND motion_after<=motion_before)::text FROM m_razhin.gpo_29_metrica_query$$,
 $$SELECT true::text$$),
('query_optimization',30,2,'Before/after отчёт полный',
 $$SELECT (count(*)>=5 AND bool_and(metric_name IS NOT NULL
 AND before_value IS NOT NULL AND after_value IS NOT NULL
 AND verdict IS NOT NULL))::text FROM m_razhin.gpo_30_report$$,
 $$SELECT true::text$$);
