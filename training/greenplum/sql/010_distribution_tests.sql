CREATE TABLE IF NOT EXISTS greenplum_training.dist_source (
    event_id bigint,
    event_date date,
    user_id bigint,
    country text,
    city text,
    hot_key text,
    nullable_key integer,
    payload text
)
DISTRIBUTED BY (event_id);

TRUNCATE greenplum_training.dist_source;
INSERT INTO greenplum_training.dist_source
SELECT
    n,
    DATE '2025-01-01' + (n % 90)::integer,
    1 + n % 20000,
    (ARRAY['RU','BR','US','IN','CN','DE','FR','GB'])[
        1 + (n % 8)::integer
    ],
    'city_' || (n % 200),
    CASE WHEN n <= 80000 THEN 'HOT' ELSE 'key_' || n END,
    CASE WHEN n % 5 = 0 THEN NULL ELSE (n % 1000)::integer END,
    repeat(md5(n::text), 1 + (n % 4)::integer)
FROM generate_series(1,100000) n;

CREATE TABLE IF NOT EXISTS greenplum_training.dist_dimension (
    country text,
    country_name text,
    region text
)
DISTRIBUTED BY (country);

TRUNCATE greenplum_training.dist_dimension;
INSERT INTO greenplum_training.dist_dimension VALUES
('RU','Russia','Europe'),('BR','Brazil','South America'),
('US','United States','North America'),('IN','India','Asia'),
('CN','China','Asia'),('DE','Germany','Europe'),
('FR','France','Europe'),('GB','United Kingdom','Europe');

CREATE OR REPLACE FUNCTION greenplum_training.motion_count(p_query text)
RETURNS integer LANGUAGE plpgsql VOLATILE AS $$
DECLARE line text; result integer := 0;
BEGIN
  FOR line IN EXECUTE 'EXPLAIN ' || p_query LOOP
    IF line LIKE '%Motion%' THEN result := result + 1; END IF;
  END LOOP;
  RETURN result;
END $$;

CREATE OR REPLACE FUNCTION greenplum_training.relation_exists(p_name text)
RETURNS boolean LANGUAGE sql STABLE AS $$
SELECT to_regclass(p_name) IS NOT NULL
$$;

DELETE FROM greenplum_training.task_tests WHERE module_name='distribution';
INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql)
SELECT 'distribution',n,1,'Объект создан с точным именем',
       format('SELECT greenplum_training.relation_exists(%L)::text',
              format('m_razhin.gpd_%s_%s',lpad(n::text,2,'0'),suffix)),
       'SELECT true::text'
FROM (VALUES
(1,'segment_rows'),(2,'random'),(3,'by_event'),(4,'by_country'),
(5,'by_hot_key'),(6,'distribution'),(7,'skew_ratio'),
(8,'skew_coefficient'),(9,'null_key'),(10,'composite'),
(11,'replicated_dim'),(12,'dim_hash'),(13,'fact_country'),
(14,'colocated_join'),(15,'replicated_join'),(16,'motion_plan'),
(17,'colocated_plan'),(18,'random_join'),(19,'group_motion'),
(20,'local_group'),(21,'filter_skew'),(22,'join_skew'),
(23,'size_by_segment'),(24,'rows_vs_bytes'),(25,'metrica_profile'),
(26,'metrica_candidate'),(27,'metrica_skew'),(28,'query_motion'),
(29,'redistribute'),(30,'recommendation')) x(n,suffix);

INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql) VALUES
('distribution',2,2,'Random policy',
 $$SELECT pg_get_table_distributedby('m_razhin.gpd_02_random'::regclass)$$,
 $$SELECT 'DISTRIBUTED RANDOMLY'::text$$),
('distribution',3,2,'Распределение по event_id',
 $$SELECT pg_get_table_distributedby('m_razhin.gpd_03_by_event'::regclass)$$,
 $$SELECT 'DISTRIBUTED BY (event_id)'::text$$),
('distribution',4,2,'Распределение по country',
 $$SELECT pg_get_table_distributedby('m_razhin.gpd_04_by_country'::regclass)$$,
 $$SELECT 'DISTRIBUTED BY (country)'::text$$),
('distribution',5,2,'Распределение по hot_key',
 $$SELECT pg_get_table_distributedby('m_razhin.gpd_05_by_hot_key'::regclass)$$,
 $$SELECT 'DISTRIBUTED BY (hot_key)'::text$$),
('distribution',9,2,'Распределение по nullable_key',
 $$SELECT pg_get_table_distributedby('m_razhin.gpd_09_null_key'::regclass)$$,
 $$SELECT 'DISTRIBUTED BY (nullable_key)'::text$$),
('distribution',10,2,'Составной ключ',
 $$SELECT pg_get_table_distributedby('m_razhin.gpd_10_composite'::regclass)$$,
 $$SELECT 'DISTRIBUTED BY (country, user_id)'::text$$);

INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql) VALUES
('distribution',1,2,'Все строки учтены по сегментам',
 $$SELECT (sum(rows_count)=100000 AND count(*)=4)::text FROM m_razhin.gpd_01_segment_rows$$,
 $$SELECT true::text$$),
('distribution',6,2,'Профиль hot-key таблицы полный',
 $$SELECT (sum(rows_count)=100000 AND count(*)=4)::text FROM m_razhin.gpd_06_distribution$$,
 $$SELECT true::text$$),
('distribution',7,2,'Skew ratio совпадает с фактическим',
 $$SELECT (abs(skew_ratio-(
   SELECT round(max(c)::numeric/avg(c),4)
   FROM (SELECT count(*) c FROM m_razhin.gpd_05_by_hot_key GROUP BY gp_segment_id) s
 ))<0.0001)::text FROM m_razhin.gpd_07_skew_ratio$$,
 $$SELECT true::text$$),
('distribution',8,2,'Коэффициент skew неотрицателен',
 $$SELECT (skew_coefficient>=0)::text FROM m_razhin.gpd_08_skew_coefficient$$,
 $$SELECT true::text$$),
('distribution',11,2,'Справочник реплицирован',
 $$SELECT pg_get_table_distributedby('m_razhin.gpd_11_replicated_dim'::regclass)$$,
 $$SELECT 'DISTRIBUTED REPLICATED'::text$$),
('distribution',12,2,'Hash-справочник распределён по коду',
 $$SELECT pg_get_table_distributedby('m_razhin.gpd_12_dim_hash'::regclass)$$,
 $$SELECT 'DISTRIBUTED BY (country_code)'::text$$),
('distribution',13,2,'Факт распределён по country',
 $$SELECT pg_get_table_distributedby('m_razhin.gpd_13_fact_country'::regclass)$$,
 $$SELECT 'DISTRIBUTED BY (country)'::text$$),
('distribution',14,2,'Colocated JOIN не теряет строки',
 $$SELECT (count(*)=100000)::text FROM m_razhin.gpd_14_colocated_join$$,
 $$SELECT true::text$$),
('distribution',15,2,'JOIN с replicated dimension не теряет строки',
 $$SELECT (count(*)=100000)::text FROM m_razhin.gpd_15_replicated_join$$,
 $$SELECT true::text$$),
('distribution',16,2,'Количество Motion измерено',
 $$SELECT (motion_count=greenplum_training.motion_count(
 'SELECT * FROM greenplum_training.dist_source a JOIN greenplum_training.dist_dimension b USING(country)'
 ))::text FROM m_razhin.gpd_16_motion_plan$$,
 $$SELECT true::text$$),
('distribution',17,2,'Colocated план лучше несовместимого',
 $$SELECT (motion_count<=(SELECT motion_count FROM m_razhin.gpd_16_motion_plan))::text
 FROM m_razhin.gpd_17_colocated_plan$$,
 $$SELECT true::text$$),
('distribution',18,2,'Random fact имеет random policy',
 $$SELECT pg_get_table_distributedby('m_razhin.gpd_18_random_join'::regclass)$$,
 $$SELECT 'DISTRIBUTED RANDOMLY'::text$$),
('distribution',19,2,'GROUP BY по чужому ключу измерен',
 $$SELECT (motion_count=greenplum_training.motion_count(
 'SELECT country,count(*) FROM greenplum_training.dist_source GROUP BY country'
 ))::text FROM m_razhin.gpd_19_group_motion$$,
 $$SELECT true::text$$),
('distribution',20,2,'Локальный GROUP BY имеет не больше Motion',
 $$SELECT (motion_count<=(SELECT motion_count FROM m_razhin.gpd_19_group_motion))::text
 FROM m_razhin.gpd_20_local_group$$,
 $$SELECT true::text$$),
('distribution',29,2,'Улучшенная копия не использует hot_key',
 $$SELECT (pg_get_table_distributedby('m_razhin.gpd_29_redistribute'::regclass)
 <> 'DISTRIBUTED BY (hot_key)')::text$$,
 $$SELECT true::text$$);

INSERT INTO greenplum_training.task_tests
(module_name,task_no,test_no,test_name,actual_sql,expected_sql) VALUES
('distribution',21,2,'Фильтр RU полностью профилирован',
 $$SELECT (sum(rows_count)=12500 AND count(*) BETWEEN 1 AND 4)::text
 FROM m_razhin.gpd_21_filter_skew$$,
 $$SELECT true::text$$),
('distribution',22,2,'Skew результата JOIN измерен по сегментам',
 $$SELECT (count(*) BETWEEN 1 AND 4 AND min(rows_count)>=0)::text
 FROM m_razhin.gpd_22_join_skew$$,
 $$SELECT true::text$$),
('distribution',23,2,'Размер получен для каждого primary content',
 $$SELECT (count(*)=4 AND min(size_bytes)>0)::text
 FROM m_razhin.gpd_23_size_by_segment$$,
 $$SELECT true::text$$),
('distribution',24,2,'Доли строк и байтов нормированы',
 $$SELECT (abs(sum(row_share)-1)<0.001 AND abs(sum(byte_share)-1)<0.001)::text
 FROM m_razhin.gpd_24_rows_vs_bytes$$,
 $$SELECT true::text$$),
('distribution',25,2,'Профиль содержит четыре кандидата',
 $$SELECT (count(*)=4 AND count(DISTINCT column_name)=4
 AND min(total_rows)>0 AND min(distinct_values)>0)::text
 FROM m_razhin.gpd_25_metrica_profile$$,
 $$SELECT true::text$$),
('distribution',26,2,'Выборка Метрики является внутренней таблицей',
 $$SELECT (c.relkind='r' AND x.location IS NULL)::text
 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
 LEFT JOIN pg_exttable x ON x.reloid=c.oid
 WHERE n.nspname='m_razhin' AND c.relname='gpd_26_metrica_candidate'$$,
 $$SELECT true::text$$),
('distribution',27,2,'Skew ratio выборки рассчитан',
 $$SELECT (skew_ratio>=1 AND segment_count=4)::text
 FROM m_razhin.gpd_27_metrica_skew$$,
 $$SELECT true::text$$),
('distribution',28,2,'Motion типового запроса измерен',
 $$SELECT (motion_count>=0)::text FROM m_razhin.gpd_28_query_motion$$,
 $$SELECT true::text$$),
('distribution',30,2,'Итог сравнивает три физических варианта',
 $$SELECT (count(*)=3 AND count(DISTINCT table_name)=3
 AND bool_and(policy IS NOT NULL AND skew_ratio>=1
 AND motion_count>=0 AND verdict IS NOT NULL))::text
 FROM m_razhin.gpd_30_recommendation$$,
 $$SELECT true::text$$);
