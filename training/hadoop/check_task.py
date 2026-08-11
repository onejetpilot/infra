#!/usr/bin/env python3
"""Structural Hadoop course checker, executed inside Jupyter."""
import json, os, subprocess, sys

module, task = sys.argv[1], int(sys.argv[2])
user = os.environ.get("HDFS_USER", os.environ.get("HADOOP_USER_NAME", "student"))
db = os.environ.get("HADOOP_TRAINING_DB", user.replace(".", "_").replace("-", "_") + "_db")
training_root = os.environ.get("HADOOP_TRAINING_ROOT", f"/user/{user}/hadoop_training")

def run(args):
    return subprocess.run(args, text=True, capture_output=True)

evidence_path = f"{training_root}/evidence/{module}/task_{task:02d}.json"
evidence_result = run(["hdfs", "dfs", "-cat", evidence_path])
try:
    evidence = json.loads(evidence_result.stdout) if evidence_result.returncode == 0 else {}
except json.JSONDecodeError:
    evidence = {}
evidence_ok = (
    evidence.get("module") == module and evidence.get("task") == task
    and len(str(evidence.get("command", "")).strip()) >= 8
    and len(str(evidence.get("observation", "")).strip()) >= 20
    and len(str(evidence.get("explanation", "")).strip()) >= 40
)

if module in {"hdfs_model", "hdfs_cli", "formats", "operations"}:
    path = f"{training_root}/{module}/task_{task:02d}"
    exists = run(["hdfs", "dfs", "-test", "-e", path]).returncode == 0
    count = run(["hdfs", "dfs", "-count", path])
    nonempty = count.returncode == 0 and int(count.stdout.split()[1]) + int(count.stdout.split()[0]) > 0
    checks = [("Артефакт существует", exists), ("Артефакт не пуст", nonempty)]
else:
    name = {"hive_ddl":"hv", "partitioning":"pt", "etl_quality":"dq", "capstone":"cp"}[module] + f"_{task:02d}"
    url = f"jdbc:hive2://hiveserver2:10000/{db}"
    base = ["beeline", "-u", url, "-n", user, "--silent=true", "--showHeader=false", "--outputformat=tsv2"]
    show = run(base + ["-e", f"SHOW TABLES IN `{db}` LIKE '{name}';"])
    exists = show.returncode == 0 and name in show.stdout.split()
    query = run(base + ["-e", f"SELECT * FROM `{db}`.`{name}` LIMIT 1;"]) if exists else None
    checks = [("Hive-объект существует", exists), ("Hive-объект читается", bool(query and query.returncode == 0))]

checks.append(("Сохранено содержательное доказательство", evidence_ok))

for label, ok in checks:
    print(("PASS" if ok else "FAIL") + " | " + label)
sys.exit(0 if all(ok for _, ok in checks) else 1)
