.PHONY: up down status logs init upload jupyter test reset
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
test:
	bash scripts/smoke-test.sh
reset:
	CONFIRM_RESET=DELETE bash scripts/reset-lab.sh
