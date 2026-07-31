CREATE DATABASE IF NOT EXISTS yndx_metrica_data;

CREATE EXTERNAL TABLE IF NOT EXISTS yndx_metrica_data.metrica (
    `_date` string,
    dt string,
    visitid string,
    isnewuser bigint,
    starturl string,
    endurl string,
    pageviews bigint,
    visitduration bigint,
    regioncountry string,
    regioncity string,
    clientid string,
    ipaddress string,
    clienttimezone bigint,
    devicecategory bigint,
    mobilephone string,
    mobilephonemodel string,
    operatingsystem string,
    browser string
)
PARTITIONED BY (`date` string)
STORED AS PARQUET
LOCATION 'hdfs://namenode:8020/data/raw/yndx_metrica/parquet'
TBLPROPERTIES (
    'bucketing_version'='2',
    'parquet.column.index.access'='true'
);

MSCK REPAIR TABLE yndx_metrica_data.metrica;
