"""Snowflake ETL template; mappings are deliberately not fabricated."""
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("ebay-snowflake").enableHiveSupport().getOrCreate()
source = spark.table("m_razhin_db.ebay_listings_optimized")
raise NotImplementedError("Define keys and mappings for fact/dimension tables from the actual schema")

