# Что скринить

## 1. Файлы

Показать папки `src`, `dags`, `sql`.

Комментарий: «Здесь лежат producer, consumer, два DAG-а и SQL».

## 2. Исходные данные

Открыть CSV и выполнить:

```powershell
docker compose exec -T kafka-task-db psql -U kafka_user -d kafka_task -c "TABLE kafka_prod.events_source;"
```

Комментарий: «Это исходные данные до очистки».

## 3. Kafka-топик

```powershell
docker compose exec -T kafka kafka-topics.sh --bootstrap-server kafka:29092 --describe --topic task_events_log_razhin
```

Комментарий: «Топик создан и готов к работе».

## 4. Producer

В Airflow показать DAG producer, время 08:00 и зелёный запуск.

Комментарий: «Producer отправил новые строки в Kafka».

## 5. Consumer

В Airflow показать DAG consumer, время 19:00 и зелёный запуск.

Комментарий: «Consumer прочитал и проверил данные».

## 6. Результат

```powershell
docker compose exec -T kafka-task-db psql -U kafka_user -d kafka_task -c "TABLE kafka_dev.events_log_razhin;"
```

Комментарий: «Здесь остались только корректные строки».

## 7. Повторный запуск

Ещё раз запустить producer и показать `No new rows after id=12`.

Комментарий: «При повторном запуске дублей нет».
