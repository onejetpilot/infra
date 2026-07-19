from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("print-ebay-schema").enableHiveSupport().getOrCreate()
spark.read.parquet("hdfs://namenode:8020/user/m.razhin/ebay").printSchema()
spark.stop()

