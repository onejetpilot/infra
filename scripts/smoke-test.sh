#!/usr/bin/env bash
set -uo pipefail
pass=0; fail=0
check() { local name="$1"; shift; if "$@" >/tmp/smoke.out 2>&1; then printf 'PASS  %s\n' "$name"; ((pass++)); else printf 'FAIL  %s: %s\n' "$name" "$(tail -n 1 /tmp/smoke.out)"; ((fail++)); fi; }
check "1. Контейнеры запущены" docker compose ps --status running
check "2. NameNode доступен" docker compose exec -T namenode hdfs dfs -test -d /
check "3. Два DataNode" bash -c '[[ $(docker compose exec -T namenode hdfs dfsadmin -report | grep -c "Name: ") -eq 2 ]]'
check "4-5. HDFS файл, replication=2" bash -c 'echo smoke | docker compose exec -T namenode bash -c '\''p="/user/${HDFS_USER:-student}/.smoke"; hdfs dfs -mkdir -p "$p" && hdfs dfs -setfacl -m user:hive:rwx "$p" && hdfs dfs -put -f - "$p/file" && hdfs dfs -setrep -w 2 "$p/file"'\'''
check "6. PostgreSQL" docker compose exec -T postgres pg_isready -U hive -d metastore
check "7. Hive Metastore" docker compose exec -T hive-metastore bash -c '</dev/tcp/localhost/9083'
check "8-10. HiveServer2 и тестовая Parquet table" docker compose exec -T hiveserver2 bash -c 'u="${HDFS_USER:-student}"; beeline -u jdbc:hive2://localhost:10000/default -n "$u" --silent=true -e "CREATE DATABASE IF NOT EXISTS smoke_db; CREATE EXTERNAL TABLE IF NOT EXISTS smoke_db.t(id INT) STORED AS PARQUET LOCATION '\''/user/$u/.smoke/table'\''; SHOW TABLES IN smoke_db;"'
check "11-14. Spark master/HDFS/HMS/Parquet" docker compose exec -T spark-master spark-submit --master spark://spark-master:7077 /opt/lab/spark/03_smoke_test.py
check "15. Zeppelin HTTP" curl -fsS http://localhost:8080/api/version
check "16. Notebook volume mounted" docker compose exec -T zeppelin test -w /opt/zeppelin/notebook
printf '\nИТОГ: PASS=%d FAIL=%d\n' "$pass" "$fail"
(( fail == 0 ))
