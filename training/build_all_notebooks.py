"""Rebuild every training notebook and apply deep-theory layers."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parent
scripts=[R/'common/scripts/build_data_catalog.py',R/'sql/scripts/build_functions_notebook.py',R/'sql/scripts/build_procedures_notebook.py',R/'sql/scripts/build_deduplication_notebook.py',R/'sql/scripts/build_transactions_notebook.py',R/'sql/scripts/build_window_functions_notebook.py',R/'sql/scripts/build_remaining_sql_course.py',R/'greenplum/scripts/build_course_intro.py',R/'greenplum/scripts/build_distribution_notebook.py',R/'greenplum/scripts/build_storage_partitioning_notebook.py',R/'greenplum/scripts/build_query_optimization_notebook.py',R/'greenplum/scripts/build_gpfdist_notebook.py',R/'greenplum/scripts/build_pxf_hdfs_notebook.py',R/'greenplum/scripts/build_etl_notebook.py',R/'greenplum/scripts/build_data_marts_notebook.py',R/'greenplum/scripts/build_administration_notebook.py',R/'hadoop/scripts/build_hadoop_course.py',R/'spark/scripts/build_spark_course.py',R/'sql/scripts/enhance_sql_theory.py',R/'greenplum/scripts/enhance_greenplum_theory.py',R/'hadoop/scripts/enhance_hadoop_theory.py',R/'spark/scripts/enhance_spark_theory.py',R/'common/scripts/enhance_course_maps.py']
for script in scripts:
 print('BUILD',script.relative_to(R),flush=True);subprocess.run([sys.executable,str(script)],check=True)
print('All training notebooks rebuilt successfully.')
