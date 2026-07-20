import os
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("lab-smoke-test").enableHiveSupport().getOrCreate()
assert spark.sparkContext.master.startswith("spark://")
user = os.environ.get("HDFS_USER", "student")
database = "".join(c if c.isalnum() or c == "_" else "_" for c in user) + "_db"
path = f"hdfs://namenode:8020/user/{user}/.smoke/spark-parquet"
spark.range(3).write.mode("overwrite").parquet(path)
assert spark.read.parquet(path).count() == 3
assert database in [x.name for x in spark.catalog.listDatabases()]
spark.stop()
