import os, sys
from pyspark.sql import SparkSession

ROOT='hdfs://namenode:8020/tmp/spark-training-course-qa'
os.environ['SPARK_TRAINING_ROOT']=ROOT
sys.path.insert(0,'/opt/lab/spark-training')
from check_task import check_task,save_evidence

spark=SparkSession.builder.appName('spark-course-checker-qa').getOrCreate()
fs=spark._jvm.org.apache.hadoop.fs.FileSystem.get(spark._jsc.hadoopConfiguration())
path=spark._jvm.org.apache.hadoop.fs.Path(ROOT)
try:
    fs.delete(path,True)
    try:
        check_task(spark,'foundations',1)
        raise AssertionError('Empty task unexpectedly passed')
    except AssertionError as error:
        if str(error)=='Empty task unexpectedly passed': raise
    spark.createDataFrame([(1,'ok')],['id','status']).write.mode('overwrite').parquet(f'{ROOT}/foundations/task_01')
    save_evidence(spark,'foundations',1,'select and write parquet','Получена одна строка с двумя типизированными колонками','Spark выполнил action, записал Parquet в HDFS и повторно прочитал его через DataFrameReader.')
    check_task(spark,'foundations',1)
    print('spark_checker_qa=OK')
finally:
    fs.delete(path,True)
    spark.stop()
