# Kafka + Airflow

Здесь находится только инфраструктурная основа задания:

- `sql` — создание `kafka_prod`, `kafka_dev` и `events_source`;
- `src` — место для собственного producer и consumer;
- `dags` — место для собственных DAG-файлов.

Топик `task_events_log_razhin` создается сервисом `kafka-init` из общего Compose.
Готового решения задания в проекте нет.
