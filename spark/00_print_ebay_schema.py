from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("print-ebay-schema").enableHiveSupport().getOrCreate()
spark.read.parquet("hdfs://namenode:8020/data/raw/ebay").printSchema()
spark.stop()
