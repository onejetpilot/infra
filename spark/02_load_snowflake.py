"""Snowflake ETL template; mappings are deliberately not fabricated."""
import os
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("ebay-snowflake").enableHiveSupport().getOrCreate()
user = os.environ.get("HDFS_USER", "student")
database = "".join(c if c.isalnum() or c == "_" else "_" for c in user) + "_db"
source = spark.table(f"{database}.ebay_listings_optimized")
raise NotImplementedError("Define keys and mappings for fact/dimension tables from the actual schema")
