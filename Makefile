.PHONY: up down status logs init upload jupyter kafka-check test reset
up:
	docker compose up -d --build
down:
	docker compose down
status:
	docker compose ps
logs:
	docker compose logs -f
init:
	docker compose exec -T namenode bash /opt/lab/scripts/init-hdfs.sh
	docker compose exec -T hiveserver2 bash /opt/lab/scripts/init-hive.sh
upload:
	docker compose exec -T namenode bash /opt/lab/scripts/upload-data.sh
jupyter:
	docker compose up -d --build jupyter
kafka-check:
	docker compose exec -T kafka-task-db pg_isready -U kafka_user -d kafka_task
	docker compose exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:29092 --describe --topic task_events_log_razhin
	docker compose exec -T airflow-webserver airflow dags list-import-errors
test:
	bash scripts/smoke-test.sh
reset:
	CONFIRM_RESET=DELETE bash scripts/reset-lab.sh
