"""Эталонные решения курса Greenplum: модуль Distribution."""

SOLUTIONS = {
1: ("""DROP VIEW IF EXISTS m_razhin.gpd_01_segment_rows;
CREATE VIEW m_razhin.gpd_01_segment_rows AS
SELECT gp_segment_id AS segment_id,count(*) AS rows_count
FROM greenplum_training.dist_source
GROUP BY gp_segment_id;""", "Системное поле gp_segment_id показывает primary-сегмент; одна строка результата — один сегмент."),
2: ("""DROP TABLE IF EXISTS m_razhin.gpd_02_random;
CREATE TABLE m_razhin.gpd_02_random AS
SELECT * FROM greenplum_training.dist_source
DISTRIBUTED RANDOMLY;""", "CTAS копирует 100000 событий, а RANDOMLY не связывает размещение с бизнес-ключом."),
3: ("""DROP TABLE IF EXISTS m_razhin.gpd_03_by_event;
CREATE TABLE m_razhin.gpd_03_by_event AS
SELECT * FROM greenplum_training.dist_source
DISTRIBUTED BY (event_id);""", "Уникальный event_id даёт высокую кардинальность и обычно равномерный hash distribution."),
4: ("""DROP TABLE IF EXISTS m_razhin.gpd_04_by_country;
CREATE TABLE m_razhin.gpd_04_by_country AS
SELECT * FROM greenplum_training.dist_source
DISTRIBUTED BY (country);""", "Всего восемь значений country, поэтому ключ полезен для JOIN, но слабее для баланса."),
5: ("""DROP TABLE IF EXISTS m_razhin.gpd_05_by_hot_key;
CREATE TABLE m_razhin.gpd_05_by_hot_key AS
SELECT * FROM greenplum_training.dist_source
DISTRIBUTED BY (hot_key);""", "Значение HOT встречается у 80% строк и намеренно создаёт сильный перекос."),
6: ("""DROP VIEW IF EXISTS m_razhin.gpd_06_distribution;
CREATE VIEW m_razhin.gpd_06_distribution AS
WITH segments AS (
 SELECT content AS segment_id FROM gp_segment_configuration
 WHERE role='p' AND content>=0
), counts AS (
 SELECT gp_segment_id AS segment_id,count(*) AS rows_count
 FROM m_razhin.gpd_05_by_hot_key GROUP BY gp_segment_id
)
SELECT s.segment_id,coalesce(c.rows_count,0) AS rows_count
FROM segments s LEFT JOIN counts c USING(segment_id);""", "Список primary content сохраняет даже пустой сегмент, поэтому профиль skew не занижен."),
7: ("""DROP VIEW IF EXISTS m_razhin.gpd_07_skew_ratio;
CREATE VIEW m_razhin.gpd_07_skew_ratio AS
WITH counts AS (
 SELECT count(*)::numeric AS rows_count
 FROM m_razhin.gpd_05_by_hot_key GROUP BY gp_segment_id
)
SELECT round(max(rows_count)/avg(rows_count),4) AS skew_ratio FROM counts;""", "max/avg равен 1 при идеальном балансе и растёт вместе с перегрузкой крупнейшего сегмента."),
8: ("""DROP VIEW IF EXISTS m_razhin.gpd_08_skew_coefficient;
CREATE VIEW m_razhin.gpd_08_skew_coefficient AS
WITH counts AS (
 SELECT count(*)::numeric AS rows_count
 FROM m_razhin.gpd_05_by_hot_key GROUP BY gp_segment_id
)
SELECT round(100*stddev_pop(rows_count)/nullif(avg(rows_count),0),4) AS skew_coefficient
FROM counts;""", "Коэффициент вариации выражает стандартное отклонение counts в процентах от среднего."),
9: ("""DROP TABLE IF EXISTS m_razhin.gpd_09_null_key;
CREATE TABLE m_razhin.gpd_09_null_key AS
SELECT * FROM greenplum_training.dist_source
DISTRIBUTED BY (nullable_key);""", "Все NULL одного distribution key хешируются совместимо и могут вести себя как частое значение."),
10: ("""DROP TABLE IF EXISTS m_razhin.gpd_10_composite;
CREATE TABLE m_razhin.gpd_10_composite AS
SELECT * FROM greenplum_training.dist_source
DISTRIBUTED BY (country,user_id);""", "user_id повышает разнообразие комбинации и компенсирует низкую кардинальность country."),
11: ("""DROP TABLE IF EXISTS m_razhin.gpd_11_replicated_dim;
CREATE TABLE m_razhin.gpd_11_replicated_dim AS
SELECT country AS country_code,country_name,region
FROM greenplum_training.dist_dimension
DISTRIBUTED REPLICATED;""", "Восемь строк справочника копируются на каждый primary и доступны локально для любого факта."),
12: ("""DROP TABLE IF EXISTS m_razhin.gpd_12_dim_hash;
CREATE TABLE m_razhin.gpd_12_dim_hash AS
SELECT country AS country_code,country_name,region
FROM greenplum_training.dist_dimension
DISTRIBUTED BY (country_code);""", "Hash-вариант нужен для colocated JOIN с фактом, распределённым совместимо по country."),
13: ("""DROP TABLE IF EXISTS m_razhin.gpd_13_fact_country;
CREATE TABLE m_razhin.gpd_13_fact_country AS
SELECT * FROM greenplum_training.dist_source
DISTRIBUTED BY (country);""", "Distribution key факта совпадает с ключом будущего JOIN со справочником."),
14: ("""DROP VIEW IF EXISTS m_razhin.gpd_14_colocated_join;
CREATE VIEW m_razhin.gpd_14_colocated_join AS
SELECT f.*,d.country_name,d.region
FROM m_razhin.gpd_13_fact_country f
JOIN m_razhin.gpd_12_dim_hash d ON d.country_code=f.country;""", "Обе стороны хешируются по совместимым текстовым ключам, поэтому совпадающие строки уже colocated."),
15: ("""DROP VIEW IF EXISTS m_razhin.gpd_15_replicated_join;
CREATE VIEW m_razhin.gpd_15_replicated_join AS
SELECT f.*,d.country_name,d.region
FROM greenplum_training.dist_source f
JOIN m_razhin.gpd_11_replicated_dim d ON d.country_code=f.country;""", "Реплицированная сторона присутствует на каждом сегменте и не требует пересылки большого факта."),
16: ("""DROP VIEW IF EXISTS m_razhin.gpd_16_motion_plan;
CREATE VIEW m_razhin.gpd_16_motion_plan AS
SELECT greenplum_training.motion_count(
 'SELECT * FROM greenplum_training.dist_source a JOIN greenplum_training.dist_dimension b USING(country)'
) AS motion_count;""", "Учебная функция выполняет EXPLAIN и считает строки плана, содержащие Motion."),
17: ("""DROP VIEW IF EXISTS m_razhin.gpd_17_colocated_plan;
CREATE VIEW m_razhin.gpd_17_colocated_plan AS
SELECT greenplum_training.motion_count(
 'SELECT * FROM m_razhin.gpd_13_fact_country f JOIN m_razhin.gpd_12_dim_hash d ON d.country_code=f.country'
) AS motion_count;""", "Совместимые policies должны дать не больше Motion, чем исходный несовместимый вариант."),
18: ("""DROP TABLE IF EXISTS m_razhin.gpd_18_random_join;
CREATE TABLE m_razhin.gpd_18_random_join AS
SELECT * FROM greenplum_training.dist_source
DISTRIBUTED RANDOMLY;

SELECT greenplum_training.motion_count(
 'SELECT * FROM m_razhin.gpd_18_random_join f JOIN greenplum_training.dist_dimension d USING(country)'
) AS motion_count;""", "Random policy может быть ровной, но не гарантирует совместного размещения одинаковых country."),
19: ("""DROP VIEW IF EXISTS m_razhin.gpd_19_group_motion;
CREATE VIEW m_razhin.gpd_19_group_motion AS
SELECT greenplum_training.motion_count(
 'SELECT country,count(*) FROM greenplum_training.dist_source GROUP BY country'
) AS motion_count;""", "Источник распределён по event_id, поэтому финальному GROUP BY country обычно нужен обмен строками."),
20: ("""DROP VIEW IF EXISTS m_razhin.gpd_20_local_group;
CREATE VIEW m_razhin.gpd_20_local_group AS
SELECT greenplum_training.motion_count(
 'SELECT country,count(*) FROM m_razhin.gpd_13_fact_country GROUP BY country'
) AS motion_count;""", "Когда GROUP BY содержит distribution key, группы можно вычислять локально без перераспределения факта."),
21: ("""DROP VIEW IF EXISTS m_razhin.gpd_21_filter_skew;
CREATE VIEW m_razhin.gpd_21_filter_skew AS
SELECT gp_segment_id AS segment_id,count(*) AS rows_count
FROM m_razhin.gpd_13_fact_country
WHERE country='RU'
GROUP BY gp_segment_id;""", "Таблица распределена по country, поэтому фильтр одного значения оставляет работу только его сегменту."),
22: ("""DROP VIEW IF EXISTS m_razhin.gpd_22_join_skew;
CREATE VIEW m_razhin.gpd_22_join_skew AS
SELECT f.gp_segment_id AS segment_id,count(*) AS rows_count
FROM m_razhin.gpd_05_by_hot_key f
JOIN (SELECT 'HOT'::text AS hot_key) d USING(hot_key)
GROUP BY f.gp_segment_id;""", "JOIN сохраняет частое значение HOT; профиль результата показывает runtime skew принимающей операции."),
23: ("""DROP VIEW IF EXISTS m_razhin.gpd_23_size_by_segment;
CREATE VIEW m_razhin.gpd_23_size_by_segment AS
SELECT gp_segment_id AS segment_id,
       pg_relation_size('m_razhin.gpd_05_by_hot_key'::regclass) AS size_bytes
FROM gp_dist_random('gp_id');""", "gp_dist_random выполняет запрос системного отношения на каждом primary и возвращает локальный размер файла."),
24: ("""DROP VIEW IF EXISTS m_razhin.gpd_24_rows_vs_bytes;
CREATE VIEW m_razhin.gpd_24_rows_vs_bytes AS
WITH rows_by_segment AS (
 SELECT segment_id,rows_count::numeric FROM m_razhin.gpd_06_distribution
), bytes_by_segment AS (
 SELECT segment_id,size_bytes::numeric FROM m_razhin.gpd_23_size_by_segment
)
SELECT r.segment_id,r.rows_count,b.size_bytes,
       r.rows_count/nullif(sum(r.rows_count) OVER(),0) AS row_share,
       b.size_bytes/nullif(sum(b.size_bytes) OVER(),0) AS byte_share
FROM rows_by_segment r JOIN bytes_by_segment b USING(segment_id);""", "Обе доли нормируются на общий итог; различие показывает влияние переменной длины payload."),
25: ("""DROP VIEW IF EXISTS m_razhin.gpd_25_metrica_profile;
CREATE VIEW m_razhin.gpd_25_metrica_profile AS
WITH profile AS (
 SELECT count(*) AS total_rows,
        count(DISTINCT date) AS date_ndv,
        count(DISTINCT regioncountry) AS country_ndv,
        count(DISTINCT regioncity) AS city_ndv,
        count(DISTINCT ipaddress) AS ip_ndv
 FROM dds.ext_raw_yndx_metrica_logs
)
SELECT 'date'::text AS column_name,total_rows,date_ndv AS distinct_values FROM profile
UNION ALL SELECT 'regioncountry',total_rows,country_ndv FROM profile
UNION ALL SELECT 'regioncity',total_rows,city_ndv FROM profile
UNION ALL SELECT 'ipaddress',total_rows,ip_ndv FROM profile;""", "Один профильный scan вычисляет total rows и NDV всех четырёх кандидатов, после чего показатели разворачиваются в строки."),
26: ("""DROP TABLE IF EXISTS m_razhin.gpd_26_metrica_candidate;
CREATE TABLE m_razhin.gpd_26_metrica_candidate AS
SELECT date,dt,visitid,isnewuser,starturl,endurl,pageviews,visitduration,
       regioncountry,regioncity,clientid,ipaddress,clienttimezone,
       devicecategory,mobilephone,mobilephonemodel,operatingsystem,browser
FROM dds.ext_raw_yndx_metrica_logs
LIMIT 100000
DISTRIBUTED BY (visitid);""", "visitid имеет высокую кардинальность и выбран для баланса; поля регулярных фильтров сохраняются колонками."),
27: ("""DROP VIEW IF EXISTS m_razhin.gpd_27_metrica_skew;
CREATE VIEW m_razhin.gpd_27_metrica_skew AS
WITH segments AS (
 SELECT content AS segment_id FROM gp_segment_configuration WHERE role='p' AND content>=0
), counts AS (
 SELECT gp_segment_id AS segment_id,count(*)::numeric AS rows_count
 FROM m_razhin.gpd_26_metrica_candidate GROUP BY gp_segment_id
), full_counts AS (
 SELECT s.segment_id,coalesce(c.rows_count,0) AS rows_count
 FROM segments s LEFT JOIN counts c USING(segment_id)
)
SELECT count(*)::int AS segment_count,
       round(max(rows_count)/nullif(avg(rows_count),0),4) AS skew_ratio
FROM full_counts;""", "Четыре primary учитываются даже при нулевых counts; max/avg измеряет фактический баланс выборки."),
28: ("""DROP VIEW IF EXISTS m_razhin.gpd_28_query_motion;
CREATE VIEW m_razhin.gpd_28_query_motion AS
SELECT greenplum_training.motion_count(
 $$SELECT dt,visitid,endurl,visitduration,clientid
   FROM m_razhin.gpd_26_metrica_candidate
   WHERE date='2025-05-08' AND regioncountry='Russia'
     AND regioncity='Moscow' AND ipaddress='178.176.79.xxx'$$
) AS motion_count;""", "Обычный фильтр выполняется локально на сегментах; функция фиксирует реальный Motion выбранного плана."),
29: ("""DROP TABLE IF EXISTS m_razhin.gpd_29_redistribute;
CREATE TABLE m_razhin.gpd_29_redistribute AS
SELECT * FROM greenplum_training.dist_source
DISTRIBUTED BY (event_id);""", "Новая CTAS-копия устраняет hot_key policy, не изменяя исходную учебную таблицу."),
30: ("""DROP VIEW IF EXISTS m_razhin.gpd_30_recommendation;
CREATE VIEW m_razhin.gpd_30_recommendation AS
WITH variants AS (
 SELECT 'gpd_03_by_event'::text AS table_name,
        pg_get_table_distributedby('m_razhin.gpd_03_by_event'::regclass) AS policy,
        (SELECT max(c)::numeric/avg(c) FROM (SELECT count(*) c FROM m_razhin.gpd_03_by_event GROUP BY gp_segment_id)s) AS skew_ratio,
        greenplum_training.motion_count('SELECT * FROM m_razhin.gpd_03_by_event f JOIN greenplum_training.dist_dimension d USING(country)') AS motion_count,
        'лучший баланс'::text AS verdict
 UNION ALL
 SELECT 'gpd_04_by_country',pg_get_table_distributedby('m_razhin.gpd_04_by_country'::regclass),
        (SELECT max(c)::numeric/avg(c) FROM (SELECT count(*) c FROM m_razhin.gpd_04_by_country GROUP BY gp_segment_id)s),
        greenplum_training.motion_count('SELECT * FROM m_razhin.gpd_04_by_country f JOIN greenplum_training.dist_dimension d USING(country)'),
        'colocated JOIN, проверить skew'
 UNION ALL
 SELECT 'gpd_05_by_hot_key',pg_get_table_distributedby('m_razhin.gpd_05_by_hot_key'::regclass),
        (SELECT max(c)::numeric/avg(c) FROM (SELECT count(*) c FROM m_razhin.gpd_05_by_hot_key GROUP BY gp_segment_id)s),
        greenplum_training.motion_count('SELECT * FROM m_razhin.gpd_05_by_hot_key f JOIN greenplum_training.dist_dimension d USING(country)'),
        'не использовать: hot key'
)
SELECT table_name,policy,round(skew_ratio,4) AS skew_ratio,motion_count,verdict FROM variants;""", "Итоговая рекомендация сопоставляет policy, измеренный skew и Motion трёх физических вариантов."),
}
