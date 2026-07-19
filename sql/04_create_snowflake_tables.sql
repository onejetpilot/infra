-- Safe generator: schemas are intentionally placeholders until source fields are mapped.
-- For each name below create an EXTERNAL table with actual columns, plus snapshot_dt DATE:
-- fact_listings, dim_cat, dim_sub_cat, dim_sub_sub_cat, dim_items, dim_sellers,
-- dim_locations, dim_conditions, dim_currencies, dim_logistics
-- Template:
-- CREATE EXTERNAL TABLE m_razhin_db.<TABLE> (<REAL_COLUMNS>)
-- PARTITIONED BY (snapshot_dt DATE) STORED AS PARQUET
-- LOCATION 'hdfs://namenode:8020/user/m.razhin/ebay_snowflake/<TABLE>'
-- TBLPROPERTIES ('parquet.compression'='SNAPPY');

