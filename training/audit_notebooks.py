"""Structural acceptance test for all generated training notebooks."""
from pathlib import Path
import nbformat
R=Path(__file__).resolve().parent
courses={
 'sql':(12,'task-card-sql-v1','sql-v1'),
 'greenplum':(8,'task-card-gp-v1','gp-v1'),
 'hadoop':(8,'task-card-hadoop-v1','hadoop-v1'),
 'spark':(8,'task-card-spark-v1','spark-v1')}
tasks_total=cards_total=outputs_total=0
for course,(expected_files,marker,layer) in courses.items():
 files=sorted((R/course/'notebooks').glob('*_30_Tasks.ipynb'))
 assert len(files)==expected_files,(course,len(files),expected_files)
 for path in files:
  nb=nbformat.read(path,as_version=4)
  tasks=sum(c.cell_type=='markdown' and c.source.startswith('### Задание ') for c in nb.cells)
  cards=sum(c.cell_type=='markdown' and marker in c.source for c in nb.cells)
  theory=sum(c.metadata.get('theory_enhancer')==layer for c in nb.cells)
  outputs=sum(len(c.get('outputs',[])) for c in nb.cells if c.cell_type=='code')
  executions=sum(c.get('execution_count') is not None for c in nb.cells if c.cell_type=='code')
  assert (tasks,cards,theory,outputs,executions)==(30,30,6,0,0),(path,tasks,cards,theory,outputs,executions)
  tasks_total+=tasks;cards_total+=cards;outputs_total+=outputs
 maps=list((R/course/'notebooks').glob('00_*Course_Map.ipynb'))
 assert len(maps)==1,(course,maps)
 map_nb=nbformat.read(maps[0],as_version=4)
 assert sum(c.metadata.get('course_map_enhancer')=='v1' for c in map_nb.cells)==3
catalog=R/'common/notebooks/00_Data_Catalog_and_Schemas.ipynb'
assert catalog.exists();nbformat.read(catalog,as_version=4)
assert tasks_total==1080 and cards_total==1080 and outputs_total==0
print(f'courses=4 task_notebooks=36 tasks={tasks_total} cards={cards_total} saved_outputs={outputs_total}')
