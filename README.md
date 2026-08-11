# Локальный учебный стенд Hadoop

## Учебные курсы и каталог данных

В Jupyter доступны `sql-train`, `greenplum-train`, `hadoop-train`, `spark-train` и общий
`data-catalog`. Во всех модулях используется единый формат: цели → ментальная модель →
подробная теория → архитектура/схема данных → алгоритм → ошибки → самопроверка → 30
заданий с карточками и checker. Готовые решения и выполненные outputs не публикуются.

`data-catalog/00_Data_Catalog_and_Schemas.ipynb` описывает Olist, eBay, Yandex Metrica и
MOEX: grain, ключи, связи, типы, NULL и проверки качества.

Воспроизводимая пересборка всех ноутбуков:

```powershell
python training/build_all_notebooks.py
```

Правила авторинга: `training/common/COURSE_AUTHORING_STANDARD.md`.

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
| SQL Train PostgreSQL | localhost:15433, database `sql_train`, user `student` |
| Cloudberry Database | localhost:25432, database `moex`, user `gpadmin` |

## Cloudberry Database и PXF

Четыре узла Cloudberry входят в тот же Compose-проект `hadoop-local-lab` и одновременно
подключены к внутренней сети кластера и общей сети сервисов. PXF запускается внутри каждого
узла Cloudberry и использует `config/hadoop/core-site.xml` и `hdfs-site.xml` этого стенда.

Первичная сборка PXF выполняется при общем запуске:

```bash
docker compose up -d --build
```

Команда с `--build` предназначена для первоначального развёртывания. Для обычного запуска
уже созданного стенда используйте `docker compose up -d`, чтобы Compose не пересоздал
контейнеры Cloudberry с локальными каталогами БД.

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

После перезапуска Docker стартовый скрипт поднимает уже инициализированный кластер командой
`gpstart`, а не запускает `gpinitsystem` повторно. Зелёный статус контейнера сам по себе не
гарантирует готовность СУБД, поэтому проверяйте именно SQL-командой выше.

### Greenplum lab в Jupyter

Рабочий ноутбук находится в `notebooks/Greenplum_Lab.ipynb`. В Jupyter уже установлены
`psycopg2`, SQLAlchemy и JupySQL. Подключение из Python kernel:

```python
%load_ext sql
%sql postgresql+psycopg2://gpadmin@cbdb-coordinator:5432/moex
```

Учебный курс Greenplum расположен в `training/greenplum` и доступен в Jupyter как
`greenplum-train`. Вводные ноутбуки:

- `00_Greenplum_Course_Map.ipynb`;
- `00_Architecture_and_Infrastructure.ipynb`.
- `01_Distribution_30_Tasks.ipynb` — 30 заданий по distribution policy,
  skew, colocated JOIN и Motion.
- `02_Storage_Partitioning_30_Tasks.ipynb` — heap/AO row/AO column,
  compression, partition pruning и Direct Partition Exchange.
- `03_Query_Plans_Optimization_30_Tasks.ipynb` — EXPLAIN ANALYZE,
  cardinality, JOIN/Motion, aggregation, sort и spill.
- `04_GPFDIST_30_Tasks.ipynb` — readable/writable external tables,
  CSV, rejected rows, parallel load и reconciliation.
- `05_PXF_HDFS_Parquet_30_Tasks.ipynb` — PXF profiles/fragments,
  Parquet pushdown, writable HDFS, round-trip и диагностика.
- `06_ETL_30_Tasks.ipynb` — full/incremental load, watermark,
  idempotency, late data, SCD, audit и retry.
- `07_Data_Marts_30_Tasks.ipynb` — fact/dimensions, SCD, MOEX top
  BUY/SELL, liquidity/price marts, serving и publish.
- `08_Administration_30_Tasks.ipynb` — topology, sessions/locks,
  storage/skew, maintenance, resources, PXF/HDFS и incident runbooks.

Решения создаются в `m_razhin`, а автоматические проверки и прогресс хранятся в
служебной схеме `greenplum_training`.

Курс содержит 8 практических модулей: 240 заданий и 480 автоматических тестов.
Готовые решения не публикуются. Для полной воспроизводимой инициализации:

```powershell
./powershell/init-greenplum-training.ps1
```

или:

```bash
./scripts/init-greenplum-training.sh
```

Для последующих SQL-ячеек используйте:

```sql
%%sql
SET search_path TO m_razhin, public;

SELECT current_database(), current_user, current_schema();
```

Подготовленные инфраструктурные источники:

| Назначение | Источник |
|---|---|
| Yandex Metrica в Hive | `yndx_metrica_data.metrica` |
| Yandex Metrica через PXF | `dds.ext_raw_yndx_metrica_logs` |
| countries.csv через gpfdist | `gpfdist://cdw:8080/countries.csv` |
| writable Parquet для лабораторной | `/data/raw/m_razhin/` |
| MOEX raw Parquet | `/moex_labs/raw/trades/` |

Hive-таблица `yndx_metrica_data.metrica` повторяет кластерную схему: `_date` содержит полную
дату визита, а партиционное поле `date` — год. В локальных Parquet первая физическая колонка
называется `date`; свойство Hive `parquet.column.index.access=true` сопоставляет её с `_date`
по позиции и не смешивает с годовой партицией. В PXF-источнике поле полной даты называется
`date`, как в исходной Greenplum-таблице из задания.

`gpfdist` запускается внутри координатора `cbdb-cdw3` на внутреннем порту `8080`; отдельный
Greenplum или Hadoop для него не создаётся. Файл на хосте расположен в
`data/gpfdist/countries.csv`. Файл содержит строку заголовка и 173 записи с данными.

Для чтения результата, только что записанного через writable PXF, указывайте файловый шаблон:

```sql
LOCATION (
    'pxf://data/raw/m_razhin/<directory>/*?PROFILE=hdfs:parquet'
)
```

PXF 1.6.0 может закэшировать ещё не существующий каталог, если попытаться прочитать его до
первой записи. Сначала выполните `INSERT` во writable external table, затем создавайте или
опрашивайте readable external table.

Ноутбук содержит выполненное решение пунктов 0–5 и создаёт следующие основные объекты:

| Пункт | Объекты |
|---|---|
| Distribution | `m_razhin.yndx_metrica_logs` |
| Exchange Partition | `m_razhin.yndx_metrica_logs_stg`, партиция `p_2026_08` |
| GPFDIST | `m_razhin.countries_ext`, `m_razhin.countries` |
| HDFS Parquet | `m_razhin.countries_hdfs_w`, `m_razhin.countries_hdfs_r` |
| MOEX mart | `m_razhin.dm_rasp_largest_deals` |

Повторный полный запуск безопасен: основные внутренние таблицы пересоздаются, а каталог
`/data/raw/m_razhin/countries_parquet` очищается непосредственно перед записью. Не запускайте
отдельно только ячейку `ADD PARTITION`, если родительская таблица не была пересоздана первой.

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

## SQL Train

PostgreSQL 17 с Olist-датасетом входит в общий Compose-проект как сервис `sql-train-db`.
Он использует существующий volume `sql-train_postgres_data` и исходные SQL/CSV из соседнего
проекта `../sql-train`.

Подключение с Windows:

```text
host: localhost
port: 15433
database: sql_train
user: student
password: sqltrain2026
```

Подключение из Jupyter:

```python
%load_ext sql
%sql postgresql+psycopg2://student:sqltrain2026@sql-train-db:5432/sql_train
```

Учебные материалы хранятся непосредственно в этом репозитории:

```text
training/sql/notebooks  -> Jupyter-ноутбуки
training/sql/sql        -> автоматические SQL-проверки
training/sql/scripts    -> воспроизводимые генераторы ноутбуков
```

Каталог `training/sql/notebooks` примонтирован в Jupyter как
`/opt/lab/notebooks/sql-train`. Программа рассчитана на 360 заданий: по 30 в каждом из
12 модулей. После рабочей ячейки находится сворачиваемое эталонное решение с
объяснением; результат проверяется через `training.run_checks`.

Готовые модули:

- `01_JOIN_и_гранулярность_30_Tasks.ipynb` — JOIN, кардинальность и контроль grain;
- `02_Даты_и_временные_ряды_30_Tasks.ipynb` — календарная аналитика;
- `03_Window_Functions_30_Tasks.ipynb` — окна, frames, когорты и временные ряды;
- `04_JSONB_и_массивы_PostgreSQL_30_Tasks.ipynb` — JSONB, массивы и GIN;
- `05_Functions_30_Tasks.ipynb` — функции PostgreSQL;
- `06_Procedures_30_Tasks.ipynb` — процедуры и изменяемая песочница `training`;
- `07_Transactions_Isolation_30_Tasks.ipynb` — ACID, изоляция и блокировки;
- `08_Deduplication_30_Tasks.ipynb` — канонические записи и качество;
- `09_Планы,_индексы_и_оптимизация_30_Tasks.ipynb` — EXPLAIN, индексы и планы;
- `10_SQL_ETL_и_инкрементальные_загрузки_30_Tasks.ipynb` — идемпотентный ETL;
- `11_Моделирование_DWH_30_Tasks.ipynb` — факты, измерения и SCD;
- `12_Безопасность_PostgreSQL_30_Tasks.ipynb` — роли, GRANT, RLS и least privilege.

Если базу потребуется развернуть с нуля, выполните:

```powershell
./powershell/init-sql-train.ps1
```

## HDFS и загрузка

### Spark Training

В JupyterLab доступна папка `spark-train` с курсом Apache Spark 3.5.5 на eBay:

- 8 модулей и 240 заданий;
- архитектура Spark, DataFrame API, Spark SQL, JOIN/окна, хранение,
  производительность, ETL/качество и итоговый проект;
- подробная теория без готовых решений и сохранённых результатов;
- автоматическая проверка непустого Parquet, схемы и JSON-evidence;
- выполнение на существующем master и двух worker, с HDFS и Hive Metastore.

Результаты создаются только в `/user/<HDFS_USER>/spark_training`. Начальная точка:
`spark-train/00_Spark_Course_Map.ipynb`.

### Hadoop Training

В JupyterLab доступна папка `hadoop-train` с полным курсом на реальном eBay-датасете:

- 8 последовательных модулей;
- 30 заданий в каждом, всего 240;
- подробная теория без готовых решений;
- автоматические проверки HDFS-артефактов и Hive-объектов: существование,
  читаемость/непустой результат и содержательное JSON-доказательство;
- итоговый проект raw → staging → core → quality.

Курс охватывает архитектуру HDFS, CLI, Parquet и сжатие, Hive DDL,
партиционирование и оптимизацию, права и эксплуатацию, batch ETL и качество данных.
Общий `/data/raw/ebay` используется только для чтения. Результаты создаются в
`/user/<HDFS_USER>/hadoop_training` и в личной Hive-БД `<HDFS_USER>_db`.
Начальная точка: `hadoop-train/00_Hadoop_Course_Map.ipynb`.

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
на Windows не требуется. Для Greenplum используйте `notebooks/Greenplum_Lab.ipynb`.

Для остановки только JupyterLab:

```bash
docker compose stop jupyter
```

## Kafka и Airflow

Компоненты задания входят в тот же Compose-проект и запускаются вместе с остальной
инфраструктурой:

| Компонент | Адрес / объект |
|---|---|
| PostgreSQL задания | `localhost:15434`, БД `kafka_task` |
| Исходная таблица | `kafka_prod.events_source` |
| Kafka с хоста | `localhost:9092` |
| Kafka внутри Docker | `kafka:29092` |
| Топик | `task_events_log_razhin` |
| Airflow | `http://localhost:8090` |

Локальные учетные данные по умолчанию:

| Сервис | Логин | Пароль |
|---|---|---|
| PostgreSQL `kafka_task` | `kafka_user` | `kafka2026` |
| Airflow | `airflow` | `airflow` |

Значения можно изменить в `.env` до первого запуска. Инфраструктура создает БД,
схемы `kafka_prod` и `kafka_dev`, исходную таблицу `kafka_prod.events_source` и Kafka-топик.
Итоговую таблицу, producer, consumer и DAG-и нужно написать самостоятельно по заданию.

Каталоги для работы:

- `kafka_airflow/src` — собственные producer и consumer;
- `kafka_airflow/dags` — собственные DAG-и;
- `kafka_airflow/sql` — инфраструктурная инициализация исходной БД.

Проверка готовности инфраструктуры:

```bash
make kafka-check
# Windows PowerShell:
./powershell/check-kafka-airflow.ps1
```

Проверка объектов отдельно:

```bash
docker compose exec kafka kafka-topics.sh --bootstrap-server kafka:29092 --describe --topic task_events_log_razhin
docker compose exec kafka-task-db psql -U kafka_user -d kafka_task -c "TABLE kafka_prod.events_source;"
docker compose exec airflow-webserver airflow dags list
```

## Типовые ошибки

- `Permission denied`: повторите `make init`; используются владелец/группа и режимы, не `777`.
- В `data` находятся маленькие LFS pointer-файлы: выполните `git lfs install` и `git lfs pull`.
- Новый пользователь не появился: проверьте `HDFS_USERS`, выполните `docker compose up -d`, затем `make init` и `make upload`.
- JupyterLab не открывается: проверьте `docker compose ps jupyter`, логи контейнера и свободен ли порт `8888`.
- JupyterLab запрашивает token: используйте значение `JUPYTER_TOKEN` из `.env`.
- Контейнер Cloudberry имеет статус `Up`, но SQL не отвечает: проверьте
  `docker compose logs cbdb-coordinator` и запустите существующий кластер через `gpstart -a`.
- Ошибка `PXF server ... Connection refused`: проверьте `pxf status` на обоих segment-host и
  выполните `pxf start` на узле, где сервис остановлен.
- `gpfdist` возвращает HTTP 400 при обычном `curl`: это ожидаемо без заголовка
  `X-GP-PROTO`; проверяйте его через Greenplum external table.
- Hive недоступен: проверьте `docker compose ps` и логи `postgres`, `hive-metastore`, `hiveserver2`.
- Spark не видит таблицы: проверьте `hive.metastore.uris` и `hive-site.xml` в Spark.
- Репликация не равна 2: оба DataNode должны быть healthy; используйте `dfsadmin -report` и `fsck`.
- Notes исчезают: не используйте `down -v`; проверьте mount `/opt/zeppelin/notebook`.
- Конфликт порта: измените левую часть нужного `ports` в Compose.
- `^M`/bad interpreter: `git config core.autocrlf false` либо `dos2unix scripts/*.sh docker/*/*.sh`.
- Archive не скачивается: проверьте proxy Docker Desktop и повторите build.
- Kafka недоступна: проверьте `docker compose ps kafka` и внутренний адрес `kafka:29092`.
- DAG не появился: проверьте `docker compose logs airflow-scheduler` и импорт командой
  `docker compose exec airflow-webserver airflow dags list-import-errors`.

## Backup и удаление

До удаления: `hdfs dfs -get`, `pg_dump`, и `docker compose cp zeppelin:/opt/zeppelin/notebook ./notebook-backup`.
Обычный `docker compose down` сохраняет именованные volumes Hadoop/PostgreSQL/Zeppelin, но
текущие каталоги данных Cloudberry находятся в файловой системе его контейнеров. До добавления
отдельных Cloudberry volumes не выполняйте `docker compose down` или принудительное
пересоздание `cbdb-*` без `pg_dump`.

Полное необратимое удаление: `CONFIRM_RESET=DELETE make reset` или `./powershell/reset-lab.ps1 -Confirm`.

## Ограничения

Single-host стенд без Kerberos/TLS предназначен только для локального обучения. HDFS simple authentication доверяет имени клиента. Hive использует MR fallback без Tez и рассчитан на небольшие наборы. Только успешный smoke-test подтверждает работоспособность.
