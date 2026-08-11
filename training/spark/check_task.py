"""Spark course checker used with the active SparkSession."""
import json, os

def _root():
    user=os.environ.get('HDFS_USER',os.environ.get('HADOOP_USER_NAME','student'))
    return os.environ.get('SPARK_TRAINING_ROOT',f'hdfs://namenode:8020/user/{user}/spark_training')

def check_task(spark,module,task):
    path=f'{_root()}/{module}/task_{task:02d}'
    checks=[]
    try:
        frame=spark.read.parquet(path)
        checks=[('Parquet читается',True),('Есть строки',frame.limit(1).count()==1),('Есть колонки',bool(frame.columns))]
    except Exception:
        checks=[('Parquet читается',False),('Есть строки',False),('Есть колонки',False)]
    try:
        raw='\n'.join(spark.sparkContext.textFile(f'{_root()}/evidence/{module}/task_{task:02d}.json').collect())
        e=json.loads(raw)
        ok=e.get('module')==module and e.get('task')==task and len(str(e.get('transformation','')))>=10 and len(str(e.get('observation','')))>=20 and len(str(e.get('explanation','')))>=40
    except Exception: ok=False
    checks.append(('Содержательное evidence',ok))
    for name,ok in checks: print(('PASS' if ok else 'FAIL')+' | '+name)
    if not all(ok for _,ok in checks): raise AssertionError(f'Incomplete: {module}/{task}')
    return True

def save_evidence(spark,module,task,transformation,observation,explanation):
    payload=json.dumps({'module':module,'task':task,'transformation':transformation,'observation':observation,'explanation':explanation},ensure_ascii=False)
    spark.createDataFrame([(payload,)],['value']).coalesce(1).write.mode('overwrite').text(f'{_root()}/evidence/{module}/task_{task:02d}.json')
