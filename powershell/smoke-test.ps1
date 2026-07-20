$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$pass = 0; $fail = 0
function Test-Step([string]$Name, [scriptblock]$Action) {
  try { & $Action; if ($LASTEXITCODE -ne 0) { throw "exit $LASTEXITCODE" }; Write-Host "PASS  $Name" -ForegroundColor Green; $script:pass++ }
  catch { Write-Host "FAIL  $Name : $_" -ForegroundColor Red; $script:fail++ }
}
Test-Step '1. Контейнеры' { docker compose ps --status running }
Test-Step '2. NameNode' { docker compose exec -T namenode hdfs dfs -test -d / }
Test-Step '3. Два DataNode' { $n = (docker compose exec -T namenode hdfs dfsadmin -report | Select-String '^Name:').Count; if ($n -ne 2) { throw "nodes=$n" } }
Test-Step '4-5. HDFS и replication=2' { 'smoke' | docker compose exec -T namenode bash -c 'p="/user/${HDFS_USER:-student}/.smoke"; hdfs dfs -mkdir -p "$p"; hdfs dfs -setfacl -m user:hive:rwx "$p"; hdfs dfs -put -f - "$p/file"; hdfs dfs -setrep -w 2 "$p/file"' }
Test-Step '6. PostgreSQL' { docker compose exec -T postgres pg_isready -U hive -d metastore }
Test-Step '7. Hive Metastore' { docker compose exec -T hive-metastore bash -c '</dev/tcp/localhost/9083' }
Test-Step '8-10. HiveServer2/DDL' { docker compose exec -T hiveserver2 bash -c 'u="${HDFS_USER:-student}"; beeline -u jdbc:hive2://localhost:10000/default -n "$u" --silent=true -e "CREATE DATABASE IF NOT EXISTS smoke_db; CREATE EXTERNAL TABLE IF NOT EXISTS smoke_db.t(id INT) STORED AS PARQUET LOCATION '\''/user/$u/.smoke/table'\'';"' }
Test-Step '11-14. Spark/HDFS/HMS/Parquet' { docker compose exec -T spark-master spark-submit --master spark://spark-master:7077 /opt/lab/spark/03_smoke_test.py }
Test-Step '15. Zeppelin HTTP' { curl.exe --noproxy '*' -fsS http://localhost:8080/api/version | Out-Null }
Test-Step '16. Notebook volume' { docker compose exec -T zeppelin test -w /opt/zeppelin/notebook }
Write-Host "ИТОГ: PASS=$pass FAIL=$fail"
if ($fail -gt 0) { exit 1 }
