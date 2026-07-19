from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("lab-smoke-test").enableHiveSupport().getOrCreate()
assert spark.sparkContext.master.startswith("spark://")
spark.range(3).write.mode("overwrite").parquet("hdfs://namenode:8020/user/m.razhin/.smoke/spark-parquet")
assert spark.read.parquet("hdfs://namenode:8020/user/m.razhin/.smoke/spark-parquet").count() == 3
assert "m_razhin_db" in [x.name for x in spark.catalog.listDatabases()]
spark.stop()

