"""ETL template: fill TRANSFORM after inspecting the real source schema."""
import os
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("ebay-optimized").enableHiveSupport().getOrCreate()
user = os.environ.get("HDFS_USER", "student")
database = "".join(c if c.isalnum() or c == "_" else "_" for c in user) + "_db"
source = spark.table(f"{database}.ebay_raw_parquet")
raise NotImplementedError("Define the real column mapping, then write partitioned by snapshot_dt")
