# Kafka и Airflow

Минимальное решение задания:

`events_source -> producer.py -> Kafka -> consumer.py -> events_log_razhin`

- `producer.py` отправляет новые строки;
- `consumer.py` чистит и записывает данные;
- `load_source_data.py` загружает выданный CSV;
- DAG-и запускаются в 08:00 и 19:00.

На выданных данных проходят строки `id=1` и `id=8`.
