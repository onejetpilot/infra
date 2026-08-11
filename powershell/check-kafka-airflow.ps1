$ErrorActionPreference = 'Stop'

docker compose exec -T kafka-task-db `
    pg_isready -U kafka_user -d kafka_task
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL kafka_task is unavailable' }

docker compose exec -T kafka `
    /opt/kafka/bin/kafka-topics.sh `
    --bootstrap-server kafka:29092 `
    --describe --topic task_events_log_razhin
if ($LASTEXITCODE -ne 0) { throw 'Kafka topic is unavailable' }

curl.exe --noproxy '*' -fsS http://localhost:8090/health | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Airflow is unavailable' }

docker compose exec -T airflow-webserver airflow dags list-import-errors
if ($LASTEXITCODE -ne 0) { throw 'Airflow DAG import check failed' }

Write-Host 'Kafka and Airflow infrastructure is ready.' -ForegroundColor Green
