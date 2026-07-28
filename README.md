# Локальный учебный стенд Hadoop

Стенд одной командой поднимает HDFS (1 NameNode + 2 DataNode), PostgreSQL, Hive Metastore
и HiveServer2, Spark Standalone (master + 2 worker), Zeppelin, JupyterLab и кластер
Cloudberry Database с PXF. PXF подключён к тому же HDFS — отдельного Hadoop-стека нет.

## Минимальные требования

- 64-битная Windows 10/11 с WSL2 либо Linux.
- Docker Desktop в режиме Linux containers или Docker Engine с Docker Compose v2.
- Git 2.30+ и Git LFS 3+ для получения Parquet-файлов из каталога `data`.
- Минимум 4 CPU, 16 ГБ RAM, выделенных Docker, и 25 ГБ свободного места.
- Свободные локальные порты: `7077`, `8080`–`8083`, `8888`, `9083`, `9864`, `9865`,
  `9870`, `10001`, `10002`, `15432` и `25432`.
- Доступ в интернет при первой сборке для скачивания Docker-образов и дистрибутивов.

На минимальной конфигурации Spark-задачи следует запускать последовательно. Для комфортной
работы рекомендуется 8 CPU, 40–48 ГБ RAM для Docker и не менее 30 ГБ свободного места.
Исходные данные занимают около 441 MiB, но дополнительно требуется место для образов,
постоянных Docker volumes и двух HDFS-реплик.

## Версии компонентов

- Hadoop 3.3.6, Hive 3.1.3, Spark 3.5.5, Zeppelin 0.11.2, JupyterLab 4.2.5,
  PostgreSQL 16.6, Cloudberry Database 1.6.0, PXF 1.6.0, Java 11.

Spark 3.5 поддерживает remote Hive Metastore 3.1.3, Zeppelin 0.11.2 — Spark 3.2–3.5. Hive 3.1.3 снят с upstream-поддержки, но выбран как последнее совместимое пересечение для этого учебного стека. HDFS 3.3.6 и клиенты Hadoop 3 совместимы по протоколу. Стенд намеренно не включает YARN, Tez, ZooKeeper и HA.

## Запуск

Для первого клонирования установите Git LFS и убедитесь, что файлы данных скачаны:

```bash
git lfs install
git clone <URL_РЕПОЗИТОРИЯ>
cd infra
git lfs pull
```

```bash
cp .env.example .env
# Задайте POSTGRES_PASSWORD, основной HDFS_USER и список HDFS_USERS
docker compose up -d --build
make init
make upload
make test
```

PowerShell: `Copy-Item .env.example .env`, затем `docker compose up -d --build`,
`./powershell/init-lab.ps1`, `./powershell/upload-data.ps1`, `./powershell/smoke-test.ps1`.

Состояние и логи: `docker compose ps`, `docker compose logs -f [service]`. Два узла проверяются через `docker compose exec namenode hdfs dfsadmin -report`.

## Адреса

| Сервис | Адрес |
|---|---|
| Zeppelin | http://localhost:8080 |
| JupyterLab | http://localhost:8888 |
| NameNode | http://localhost:9870 |
| DataNode 1 / 2 | http://localhost:9864 / http://localhost:9865 |
| Spark Master / workers | http://localhost:8081 / 8082 / 8083 |
| HiveServer2 / Metastore | localhost:10001 / localhost:9083 |
| PostgreSQL | localhost:15432 |
| Cloudberry Database | localhost:25432, database `moex`, user `gpadmin` |

## Cloudberry Database и PXF

Четыре узла Cloudberry входят в тот же Compose-проект `hadoop-local-lab` и одновременно
подключены к внутренней сети кластера и общей сети сервисов. PXF запускается внутри каждого
узла Cloudberry и использует `config/hadoop/core-site.xml` и `hdfs-site.xml` этого стенда.

Первичная сборка PXF выполняется при общем запуске:

```bash
docker compose up -d --build
```

После первого запуска создайте учебную БД и расширение:

```bash
docker compose exec cbdb-coordinator createdb moex
docker compose exec cbdb-coordinator psql -d moex -c "CREATE EXTENSION IF NOT EXISTS pxf;"
```

Проверка сервисов:

```bash
docker compose exec cbdb-segment-host-1 pxf status
docker compose exec cbdb-coordinator psql -d moex -c "SELECT version();"
```

Загрузка одного торгового дня MOEX для тикера `RASP` в HDFS и создание external table
`m_razhin.moex_trades_ext`:

```powershell
python -m pip install -r requirements-moex.txt
./powershell/load-moex.ps1 -Ticker RASP -TradeDate 2026-07-28
```

Parquet хранится в
`/moex_labs/raw/trades/secid=RASP/trade_session_date=2026-07-28/trades.parquet`.
Загрузчик использует Snappy, поскольку входящий в PXF 1.6.0 Hadoop-клиент собран без
нативной поддержки Zstandard.

## HDFS и загрузка

`HDFS_USER` задаёт основной аккаунт для Spark, Zeppelin и тестов. `HDFS_USERS` — список
аккаунтов через запятую, например `anna,ivan,petr`. Команда `make init` создаёт каждому
отдельные каталоги `/user/<логин>` и Hive-БД `<логин>_db`; точки и дефисы в имени БД
заменяются подчёркиваниями. Исходные наборы загружаются один раз в общий raw-слой
`/data/raw/<dataset>` и доступны всем участникам только для чтения.

Пример `.env` для трёх участников:

```dotenv
HDFS_USER=anna
HDFS_USERS=anna,ivan,petr
```

После запуска будут созданы:

```text
/data/raw/ebay                            -> общие исходные данные eBay
/data/raw/yndx_metrica/parquet            -> общие исходные данные Yandex
/data/raw/google_analytics                -> общие исходные данные Google
/user/anna/{hive,ebay_listings_optimized,ebay_snowflake} -> anna_db
/user/ivan/{hive,ebay_listings_optimized,ebay_snowflake} -> ivan_db
/user/petr/{hive,ebay_listings_optimized,ebay_snowflake} -> petr_db
```

Допустимы латинские буквы, цифры, точки, дефисы и подчёркивания; логин должен начинаться
с буквы. `HDFS_USER` должен присутствовать в `HDFS_USERS`, поскольку этот аккаунт используют
Spark, Zeppelin и smoke-тесты.

Чтобы добавить участника позднее, допишите его логин в `HDFS_USERS`, пересоздайте контейнеры
для применения окружения и повторите инициализацию:

```bash
docker compose up -d
make init
```

Добавление пользователя не копирует raw-данные повторно. `make upload` нужен только при первой
загрузке или обновлении локального каталога `data`. Уже заполненные raw-каталоги при обычной
загрузке пропускаются. Для полной замены данных только в HDFS используйте
`OVERWRITE=true make upload`; в PowerShell — `./powershell/upload-data.ps1 -Overwrite`.
Эти команды никогда не удаляют локальные файлы из каталога `data`.

```bash
docker compose exec namenode hdfs dfs -ls /
docker compose exec namenode hdfs dfs -du -s -h /data/raw/ebay
docker compose exec namenode hdfs dfs -ls /data/raw/ebay
docker compose exec namenode hdfs dfs -ls /user/student
```

Parquet-файлы в `data/ebay`, `data/yandex`, `data/google` хранятся в Git LFS и при корректно
установленном Git LFS скачиваются вместе с репозиторием. Если вместо Parquet получены маленькие
текстовые pointer-файлы, выполните `git lfs install` и `git lfs pull`. Пустые наборы при загрузке
пропускаются. Загрузчик копирует их в `/data/raw/ebay`, `/data/raw/yndx_metrica/parquet`
и `/data/raw/google_analytics`,
назначает владельца `root:supergroup`, права только на чтение и replication factor `2`.
Для физической проверки используйте `hdfs fsck /path -files -blocks -locations`.

## Hive

```bash
docker compose exec hiveserver2 beeline -u 'jdbc:hive2://localhost:10000/default' -n student
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

## JupyterLab

JupyterLab использует тот же Spark 3.5.5, Hive Metastore и HDFS, что и остальные сервисы.
Ноутбуки сохраняются на хосте в каталоге `notebooks`, поэтому не исчезают при пересоздании
контейнера. Каталог примонтирован внутрь контейнера как `/opt/lab/notebooks`.

Задайте непустой токен в `.env`:

```dotenv
JUPYTER_TOKEN=change-me-local-only
```

При общем `docker compose up -d --build` JupyterLab запускается вместе со всем стендом.
Для отдельного запуска или пересборки используйте:

```bash
make jupyter
# либо
docker compose up -d --build jupyter
```

Проверьте состояние и откройте интерфейс:

```bash
docker compose ps jupyter
docker compose logs -f jupyter
```

Адрес: `http://localhost:8888`. Введите значение `JUPYTER_TOKEN` на странице входа.
Пример первой PySpark-ячейки находится в `notebooks/README.md`. Настройки master,
Hive Metastore и HDFS уже передаются контейнеру; вручную устанавливать Java или PySpark
на Windows не требуется.

Для остановки только JupyterLab:

```bash
docker compose stop jupyter
```

## Типовые ошибки

- `Permission denied`: повторите `make init`; используются владелец/группа и режимы, не `777`.
- В `data` находятся маленькие LFS pointer-файлы: выполните `git lfs install` и `git lfs pull`.
- Новый пользователь не появился: проверьте `HDFS_USERS`, выполните `docker compose up -d`, затем `make init` и `make upload`.
- JupyterLab не открывается: проверьте `docker compose ps jupyter`, логи контейнера и свободен ли порт `8888`.
- JupyterLab запрашивает token: используйте значение `JUPYTER_TOKEN` из `.env`.
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
