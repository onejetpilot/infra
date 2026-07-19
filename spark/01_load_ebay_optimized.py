"""ETL template: fill TRANSFORM after inspecting the real source schema."""
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("ebay-optimized").enableHiveSupport().getOrCreate()
source = spark.table("m_razhin_db.ebay_raw_parquet")
raise NotImplementedError("Define the real column mapping, then write partitioned by snapshot_dt")

