# Локальный учебный стенд Hadoop

Стенд поднимает HDFS (1 NameNode + 2 DataNode), PostgreSQL, Hive Metastore и HiveServer2, Spark Standalone (master + 2 worker) и Zeppelin. Все версии фиксированы; HDFS, Metastore и ноутбуки используют постоянные volumes.

## Требования и версии

- Windows 11, WSL2, запущенный Docker Desktop в Linux containers mode, Compose v2.
- Рекомендуется выделить Docker 40–48 ГБ RAM, не менее 8 CPU и 30 ГБ диска.
- Hadoop 3.3.6, Hive 3.1.3, Spark 3.5.5, Zeppelin 0.11.2, PostgreSQL 16.6, Java 11.

Spark 3.5 поддерживает remote Hive Metastore 3.1.3, Zeppelin 0.11.2 — Spark 3.2–3.5. Hive 3.1.3 снят с upstream-поддержки, но выбран как последнее совместимое пересечение для этого учебного стека. HDFS 3.3.6 и клиенты Hadoop 3 совместимы по протоколу. Стенд намеренно не включает YARN, Tez, ZooKeeper и HA.

## Запуск

```bash
cp .env.example .env
# Измените POSTGRES_PASSWORD
docker compose up -d --build
make init
make test
```

PowerShell: `Copy-Item .env.example .env`, затем `docker compose up -d --build`, `./powershell/init-lab.ps1`, `./powershell/smoke-test.ps1`.

Состояние и логи: `docker compose ps`, `docker compose logs -f [service]`. Два узла проверяются через `docker compose exec namenode hdfs dfsadmin -report`.

## Адреса

| Сервис | Адрес |
|---|---|
| Zeppelin | http://localhost:8080 |
| NameNode | http://localhost:9870 |
| DataNode 1 / 2 | http://localhost:9864 / http://localhost:9865 |
| Spark Master / workers | http://localhost:8081 / 8082 / 8083 |
| HiveServer2 / Metastore | localhost:10001 / localhost:9083 |
| PostgreSQL | localhost:15432 |

## HDFS и загрузка

```bash
docker compose exec namenode hdfs dfs -ls /
docker compose exec namenode hdfs dfs -du -s -h /user/m.razhin/ebay
docker compose exec namenode hdfs dfs -setrep -R -w 2 /user/m.razhin/ebay
docker compose exec namenode hdfs dfs -cp /user/m.razhin/ebay/a /user/m.razhin/ebay/b
```

Положите файлы в `data/ebay`, `data/yandex`, `data/google`, затем `make upload` или `./powershell/upload-data.ps1`. Пустые каталоги пропускаются. Повторная загрузка блокируется; замена: `OVERWRITE=true make upload` либо PowerShell с `-Overwrite`. Для физической проверки используйте `hdfs fsck /path -files -blocks -locations`.

## Hive

```bash
docker compose exec hiveserver2 beeline -u 'jdbc:hive2://localhost:10000/default' -n m.razhin
```

Работают `SHOW DATABASES`, `SHOW PARTITIONS`, `MSCK REPAIR TABLE`, `DESCRIBE FORMATTED`. Схема eBay неизвестна, поэтому SQL `02`–`04` — неисполняемые шаблоны. Получите схему:

С хоста JDBC URL: `jdbc:hive2://localhost:10001/default`. Предпочтительный порт 10000 оказался занят в проверенной Windows-среде, поэтому host-порт изменён на 10001; PostgreSQL аналогично опубликован на 15432. В Docker-сети используются исходные 10000/5432.

```bash
docker compose exec spark-master spark-submit /opt/lab/spark/00_print_ebay_schema.py
```

Затем вставьте реальные поля. `snapshot_dt` задаётся только как partition column.

## Spark и Zeppelin

```bash
docker compose exec spark-master spark-submit --master spark://spark-master:7077 /opt/lab/spark/03_smoke_test.py
```

Spark использует Hive catalog, общий remote Metastore и HDFS warehouse. ETL-заготовки намеренно требуют реального mapping полей. В Zeppelin используйте `%sh`, `%spark.pyspark` и `%jdbc` (prefix `default`). Notes лежат в volume `zeppelin-notebooks`; проверьте сохранение созданием note и `docker compose restart zeppelin`.

## Типовые ошибки

- `Permission denied`: повторите `make init`; используются владелец/группа и режимы, не `777`.
- Hive недоступен: проверьте `docker compose ps` и логи `postgres`, `hive-metastore`, `hiveserver2`.
- Spark не видит таблицы: проверьте `hive.metastore.uris` и `hive-site.xml` в Spark.
- Репликация не равна 2: оба DataNode должны быть healthy; используйте `dfsadmin -report` и `fsck`.
- Notes исчезают: не используйте `down -v`; проверьте mount `/opt/zeppelin/notebook`.
- Конфликт порта: измените левую часть нужного `ports` в Compose.
- `^M`/bad interpreter: `git config core.autocrlf false` либо `dos2unix scripts/*.sh docker/*/*.sh`.
- Archive не скачивается: проверьте proxy Docker Desktop и повторите build.

## Backup и удаление

До удаления: `hdfs dfs -get`, `pg_dump`, и `docker compose cp zeppelin:/opt/zeppelin/notebook ./notebook-backup`. Обычный `docker compose down` сохраняет volumes.

Полное необратимое удаление: `CONFIRM_RESET=DELETE make reset` или `./powershell/reset-lab.ps1 -Confirm`.

## Ограничения

Single-host стенд без Kerberos/TLS предназначен только для локального обучения. HDFS simple authentication доверяет имени клиента. Hive использует MR fallback без Tez и рассчитан на небольшие наборы. Только успешный smoke-test подтверждает работоспособность.
