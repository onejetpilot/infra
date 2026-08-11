import json,os,subprocess,sys,tempfile
ROOT='/tmp/hadoop-training-course-qa'
CHECK='/opt/lab/hadoop-training/check_task.py'
def run(args,**kw):return subprocess.run(args,text=True,**kw)
def hdfs(*args,**kw):return run(['hdfs','dfs',*args],**kw)
env={**os.environ,'HADOOP_TRAINING_ROOT':ROOT}
try:
 hdfs('-rm','-r','-f',ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 negative=run(['python3',CHECK,'hdfs_model','1'],env=env,capture_output=True)
 assert negative.returncode!=0,'Empty Hadoop task unexpectedly passed'
 hdfs('-mkdir','-p',f'{ROOT}/hdfs_model/task_01',f'{ROOT}/evidence/hdfs_model',check=True)
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',delete=False) as f:
  f.write('artifact');artifact=f.name
 hdfs('-put',artifact,f'{ROOT}/hdfs_model/task_01/data.txt',check=True);os.unlink(artifact)
 evidence={'module':'hdfs_model','task':1,'command':'hdfs dfs -ls /data/raw/ebay','observation':'Обнаружены дневные partitions и Parquet-файлы eBay','explanation':'NameNode возвращает namespace, а реплицированные блоки находятся на двух DataNode.'}
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',delete=False) as f:
  json.dump(evidence,f,ensure_ascii=False);evidence_file=f.name
 hdfs('-put',evidence_file,f'{ROOT}/evidence/hdfs_model/task_01.json',check=True);os.unlink(evidence_file)
 positive=run(['python3',CHECK,'hdfs_model','1'],env=env)
 assert positive.returncode==0
 print('hadoop_checker_qa=OK')
finally:
 hdfs('-rm','-r','-f',ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
