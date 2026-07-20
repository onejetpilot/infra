import os
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("print-ebay-schema").enableHiveSupport().getOrCreate()
user = os.environ.get("HDFS_USER", "student")
spark.read.parquet(f"hdfs://namenode:8020/user/{user}/ebay").printSchema()
spark.stop()
