\set ON_ERROR_STOP on

CREATE SCHEMA IF NOT EXISTS :"student_schema";
CREATE EXTENSION IF NOT EXISTS pxf;

DROP EXTERNAL TABLE IF EXISTS :"student_schema".moex_trades_ext;

SELECT format(
    $ddl$
    CREATE READABLE EXTERNAL TABLE %I.moex_trades_ext (
        boardid text,
        board_name text,
        isin text,
        isqualifiedinvestors smallint,
        secid text,
        price numeric(20,6),
        value numeric(24,6),
        quantity bigint,
        deal_type text,
        deal_time text,
        trade_session_date date
    )
    LOCATION (%L)
    FORMAT 'CUSTOM' (FORMATTER='pxfwritable_import')
    $ddl$,
    :'student_schema',
    format(
        'pxf://moex_labs/raw/trades/secid=%s/trade_session_date=%s/*.parquet?PROFILE=hdfs:parquet&SERVER=default',
        :'ticker',
        :'trade_date'
    )
)
\gexec

SELECT count(*) AS loaded_rows
FROM :"student_schema".moex_trades_ext;
