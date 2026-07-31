CREATE SCHEMA IF NOT EXISTS dds;

DROP EXTERNAL TABLE IF EXISTS dds.ext_raw_yndx_metrica_logs;

CREATE READABLE EXTERNAL TABLE dds.ext_raw_yndx_metrica_logs (
    date text,
    dt text,
    visitid text,
    isnewuser bigint,
    starturl text,
    endurl text,
    pageviews bigint,
    visitduration bigint,
    regioncountry text,
    regioncity text,
    clientid text,
    ipaddress text,
    clienttimezone bigint,
    devicecategory bigint,
    mobilephone text,
    mobilephonemodel text,
    operatingsystem text,
    browser text
)
LOCATION (
    'pxf://data/raw/yndx_metrica/parquet/date=*/*.parquet?PROFILE=hdfs:parquet'
)
FORMAT 'CUSTOM' (FORMATTER='pxfwritable_import')
ENCODING 'UTF8';
