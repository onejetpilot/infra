import os
from pathlib import Path

import nbformat as nbf
from transaction_solutions import SOLUTIONS


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = Path(os.environ.get(
    "SQL_COURSE_OUTPUT",
    ROOT / "notebooks" / "07_Transactions_Isolation_30_Tasks.ipynb",
))

tasks = [
    ("tx_01", "В одной транзакции переведите 100 между двумя учебными счетами. Сумма балансов не должна измениться.", "BEGIN, два UPDATE, COMMIT."),
    ("tx_02", "Выполните ошибочный перевод и докажите, что после ROLLBACK оба баланса восстановились.", "После ошибки транзакция имеет состояние aborted."),
    ("tx_03", "Используйте SAVEPOINT: успешную часть оставьте, ошибочную откатите до точки сохранения.", "ROLLBACK TO SAVEPOINT не завершает внешнюю транзакцию."),
    ("tx_04", "Покажите разницу между COMMIT и ROLLBACK на training.tx_events.", "Проверяйте данные из новой команды после завершения."),
    ("tx_05", "Добавьте ограничение или проверку, не позволяющую получить отрицательный баланс.", "Инвариант должен защищаться базой, а не только приложением."),
    ("tx_06", "Сделайте перевод идемпотентным по operation_id.", "Уникальный ключ операции предотвращает повторное списание."),
    ("tx_07", "Запишите изменение баланса и аудит атомарно.", "Обе записи должны либо сохраниться, либо откатиться."),
    ("tx_08", "Используйте отложенную проверку ограничения внутри транзакции.", "SET CONSTRAINTS управляет временем проверки DEFERRABLE."),
    ("tx_09", "Создайте вложенную логику через SAVEPOINT и обработайте конфликт уникальности.", "В PostgreSQL нет настоящего вложенного BEGIN."),
    ("tx_10", "Проверьте видимость собственных незакоммиченных изменений в той же сессии.", "Сессия всегда видит собственные изменения."),
    ("tx_11", "В двух сессиях докажите, что PostgreSQL не допускает dirty read при READ UNCOMMITTED.", "В PostgreSQL READ UNCOMMITTED работает как READ COMMITTED."),
    ("tx_12", "Воспроизведите non-repeatable read при READ COMMITTED.", "Между двумя SELECT сессия B фиксирует UPDATE."),
    ("tx_13", "Повторите опыт при REPEATABLE READ и сравните второй SELECT.", "Snapshot закрепляется первым запросом транзакции."),
    ("tx_14", "Воспроизведите phantom read при READ COMMITTED.", "B вставляет строку, подходящую под предикат A."),
    ("tx_15", "Покажите отсутствие phantom read для обычного чтения при REPEATABLE READ.", "Повторный запрос читает прежний snapshot."),
    ("tx_16", "Продемонстрируйте lost update на схеме read-modify-write без блокировки.", "Два клиента читают одно значение и записывают вычисленный результат."),
    ("tx_17", "Исправьте lost update атомарным UPDATE вида balance = balance + delta.", "Вычисление происходит под блокировкой строки."),
    ("tx_18", "Исправьте lost update через SELECT ... FOR UPDATE.", "Блокировку нужно взять до чтения значения."),
    ("tx_19", "Покажите, что второй UPDATE одной строки ждёт завершения первой транзакции.", "Измерьте состояние блокировки, затем COMMIT A."),
    ("tx_20", "Получите немедленную ошибку блокировки через FOR UPDATE NOWAIT.", "NOWAIT не ждёт освобождения строки."),
    ("tx_21", "Обработайте очередь двумя воркерами через FOR UPDATE SKIP LOCKED.", "Воркеры должны выбрать разные задания."),
    ("tx_22", "Создайте deadlock, обновляя две строки в противоположном порядке.", "PostgreSQL отменит одну из транзакций."),
    ("tx_23", "Устраните deadlock единым порядком захвата строк.", "Всегда блокируйте счета по возрастанию id."),
    ("tx_24", "Установите и проверьте локальный lock_timeout.", "SET LOCAL действует только в текущей транзакции."),
    ("tx_25", "Исследуйте advisory transaction lock в двух сессиях.", "pg_try_advisory_xact_lock возвращает boolean."),
    ("tx_26", "Воспроизведите write skew при REPEATABLE READ.", "Две транзакции изменяют разные строки общего инварианта."),
    ("tx_27", "Повторите write skew при SERIALIZABLE и зафиксируйте serialization failure.", "Одну транзакцию потребуется повторить."),
    ("tx_28", "Реализуйте retry для SQLSTATE 40001 с ограничением числа попыток.", "Повторяется вся транзакция, а не последняя команда."),
    ("tx_29", "Посмотрите блокирующую и заблокированную сессии через pg_stat_activity и pg_blocking_pids.", "Для диагностики нужен pid каждой сессии."),
    ("tx_30", "Проведите итоговый конкурентный тест переводов и докажите сохранение суммы и отсутствие отрицательных балансов.", "Проверяйте инварианты после завершения всех потоков."),
]


def md(value):
    return nbf.v4.new_markdown_cell(value)


def code(value):
    return nbf.v4.new_code_cell(value)


cells = [
    md(
        "# Транзакции и изоляция PostgreSQL — 30 заданий\n\n"
        "Этот модуль использует настоящие параллельные подключения. Все эксперименты выполняются "
        "только с таблицами `training.tx_*`. Перед каждым тестом песочница восстанавливается. "
        "Не запускайте эксперименты на рабочих таблицах Olist.\n\n"
        "Готовых решений нет: шаблон управляет сессиями, а SQL-сценарий пишете вы."
    ),
    code(
        "%load_ext sql\n"
        "%config SqlMagic.displaylimit = 50\n"
        "%sql postgresql+psycopg2://student:sqltrain2026@sql-train-db:5432/sql_train"
    ),
    md(
        "## 0. Учебная схема\n\n"
        "- `training.tx_accounts` — счета и балансы;\n"
        "- `training.tx_operations` — идемпотентные операции;\n"
        "- `training.tx_events` — аудит;\n"
        "- `training.tx_jobs` — очередь для `SKIP LOCKED`;\n"
        "- `training.tx_doctors` — модель общего инварианта для write skew;\n"
        "- `training.tx_observations` — наблюдения, которые сохраняет проверяющий harness.\n\n"
        "Olist остаётся доступным для чтения, но конкурентные изменения выполняются только в песочнице."
    ),
    code(
        "%%sql\n"
        "SELECT table_name, column_name, data_type\n"
        "FROM information_schema.columns\n"
        "WHERE table_schema = 'training' AND table_name LIKE 'tx_%'\n"
        "ORDER BY table_name, ordinal_position;"
    ),
    md(
        "## 1. ACID простыми словами\n\n"
        "- **Atomicity:** последовательность изменений сохраняется целиком или не сохраняется вовсе.\n"
        "- **Consistency:** ограничения и бизнес-инварианты истинны до и после транзакции.\n"
        "- **Isolation:** параллельные транзакции не должны давать недопустимый результат.\n"
        "- **Durability:** после COMMIT данные переживают сбой процесса.\n\n"
        "`BEGIN` открывает транзакцию, `COMMIT` фиксирует, `ROLLBACK` отменяет. После SQL-ошибки "
        "PostgreSQL не разрешает продолжать обычные команды до `ROLLBACK` или отката к savepoint."
    ),
    md(
        "### Жизненный цикл транзакции\n\n"
        "Соединение и транзакция — не одно и то же. Соединение может существовать часами и "
        "последовательно выполнять много транзакций. После `BEGIN` сессия находится `in transaction`. "
        "После успешного `COMMIT` или `ROLLBACK` она снова `idle`. Если команда завершилась ошибкой, "
        "состояние становится `idle in transaction (aborted)`: до отката PostgreSQL отвечает "
        "`current transaction is aborted` на следующие команды.\n\n"
        "```text\n"
        "idle ── BEGIN ──> in transaction ── COMMIT ──> idle\n"
        "                         │\n"
        "                       ERROR\n"
        "                         ▼\n"
        "                 aborted transaction ── ROLLBACK ──> idle\n"
        "```\n\n"
        "Открытая забытая транзакция удерживает блокировки и мешает очистке старых версий строк. "
        "Поэтому `idle in transaction` — эксплуатационная проблема, а не безобидное состояние."
    ),
    md(
        "### SAVEPOINT и частичный откат\n\n"
        "`SAVEPOINT name` создаёт точку внутри текущей транзакции. `ROLLBACK TO name` отменяет "
        "изменения после неё, но не завершает внешнюю транзакцию. `RELEASE SAVEPOINT name` удаляет "
        "точку. PostgreSQL реализует это через subtransaction.\n\n"
        "```sql\n"
        "BEGIN;\n"
        "INSERT INTO ...;             -- часть 1\n"
        "SAVEPOINT optional_part;\n"
        "INSERT INTO ...;             -- часть 2, может завершиться ошибкой\n"
        "ROLLBACK TO optional_part;   -- отменится только часть 2\n"
        "COMMIT;                      -- часть 1 сохранится\n"
        "```\n\n"
        "Savepoint полезен для локально ожидаемой ошибки. Он не должен маскировать нарушение "
        "главного бизнес-инварианта: в таком случае безопаснее откатить всю транзакцию."
    ),
    md(
        "### Кто обеспечивает consistency\n\n"
        "Согласованность создаётся совместно:\n\n"
        "- типы данных не допускают значения неправильного вида;\n"
        "- `NOT NULL`, `CHECK`, `UNIQUE` и внешние ключи защищают локальные правила;\n"
        "- транзакция объединяет несколько согласованных изменений;\n"
        "- блокировки или уровень изоляции защищают правило от конкурентных изменений;\n"
        "- приложение корректно обрабатывает ошибки и повторяет транзакцию.\n\n"
        "Проверка `SELECT balance` перед `UPDATE` сама по себе ненадёжна: другая сессия может "
        "изменить баланс между этими командами. Надёжное правило должно быть выражено атомарной "
        "командой, ограничением или корректной блокировкой."
    ),
    md(
        "## 2. Уровни изоляции PostgreSQL\n\n"
        "| Уровень | Snapshot | Что важно увидеть |\n"
        "|---|---|---|\n"
        "| READ UNCOMMITTED | Реализован как READ COMMITTED | Dirty read всё равно невозможен |\n"
        "| READ COMMITTED | Новый snapshot для каждой команды | Возможны non-repeatable read и phantom |\n"
        "| REPEATABLE READ | Один snapshot транзакции | Стабильное чтение, но возможен write skew |\n"
        "| SERIALIZABLE | Serializable Snapshot Isolation | Опасная транзакция отменяется с SQLSTATE 40001 |\n\n"
        "Более строгая изоляция не означает «ошибок не будет»: приложение обязано повторять "
        "транзакции после serialization failure."
    ),
    md(
        "### MVCC: почему чтение обычно не блокирует запись\n\n"
        "PostgreSQL использует Multi-Version Concurrency Control. `UPDATE` физически создаёт новую "
        "версию строки, а старая некоторое время остаётся в таблице. Snapshot определяет, какие "
        "версии видимы конкретной команде или транзакции. Поэтому обычный `SELECT` чаще всего не "
        "мешает `UPDATE`, а `UPDATE` не заставляет читателя ждать.\n\n"
        "Упрощённо версия видима, если создавшая её транзакция уже зафиксирована для данного "
        "snapshot, а удалившая/заменившая её транзакция ещё не видима. Реализация использует "
        "идентификаторы транзакций и служебные поля tuple.\n\n"
        "MVCC не отменяет блокировки. Две записи одной строки конфликтуют, а `SELECT FOR UPDATE` "
        "намеренно превращает чтение в блокирующую операцию."
    ),
    md(
        "### Когда создаётся snapshot\n\n"
        "При `READ COMMITTED` каждая SQL-команда получает новый snapshot. Два одинаковых SELECT "
        "в одной транзакции могут увидеть разные зафиксированные состояния.\n\n"
        "При `REPEATABLE READ` snapshot закрепляется первым запросом после начала транзакции. "
        "Поздние коммиты других сессий до завершения транзакции не видны. При этом собственные "
        "изменения текущая сессия видит всегда.\n\n"
        "Следствие: важно, когда выполнен первый запрос, а не только когда написан `BEGIN`."
    ),
    md(
        "### Аномалии чтения на временной линии\n\n"
        "**Dirty read** — A видит изменение B до `COMMIT`. PostgreSQL такого не допускает даже "
        "при заявленном `READ UNCOMMITTED`.\n\n"
        "```text\n"
        "A: BEGIN ───────── SELECT balance ─────────── SELECT balance\n"
        "B:       BEGIN ─── UPDATE balance ── ROLLBACK\n"
        "```\n\n"
        "**Non-repeatable read** — A повторно читает ту же строку и видит новое значение после "
        "`COMMIT B`. Возможен при `READ COMMITTED`.\n\n"
        "```text\n"
        "A: BEGIN ─ SELECT row=old ───────────────── SELECT row=new\n"
        "B:                    UPDATE row ─ COMMIT\n"
        "```\n\n"
        "**Phantom read** — повторный запрос по предикату возвращает другое множество строк. "
        "Например, B добавила новый счёт с `balance > 1000`.\n\n"
        "```text\n"
        "A: BEGIN ─ SELECT count(*)=2 ────────────── SELECT count(*)=3\n"
        "B:                     INSERT matching row ─ COMMIT\n"
        "```\n\n"
        "При `REPEATABLE READ` PostgreSQL сохраняет snapshot и для строк, и для диапазона обычного "
        "чтения, поэтому оба последних эффекта не видны A."
    ),
    md(
        "### Lost update и write skew — это разные проблемы\n\n"
        "**Lost update** возникает, когда две сессии прочитали одно значение, независимо вычислили "
        "новое и последняя запись затёрла результат первой. Лечение: атомарный `UPDATE value = "
        "value + delta` или `SELECT FOR UPDATE` до чтения.\n\n"
        "**Write skew** затрагивает разные строки, связанные общим правилом. Например, два врача "
        "видят, что на дежурстве двое, и каждый снимает с дежурства себя. Строки разные, поэтому "
        "конфликта записи нет, но итоговый инвариант «хотя бы один врач дежурит» нарушен. "
        "`REPEATABLE READ` этого не обязан предотвращать; помогают явная блокировка общей сущности "
        "или `SERIALIZABLE` с повтором отменённой транзакции."
    ),
    md(
        "## 3. Блокировки\n\n"
        "`UPDATE` блокирует изменяемую строку. `SELECT ... FOR UPDATE` позволяет взять блокировку "
        "до вычисления нового значения. `NOWAIT` немедленно возвращает ошибку, а `SKIP LOCKED` "
        "пропускает занятые строки и подходит для очередей. Deadlock возникает, когда сессии "
        "ждут друг друга по циклу; защита — единый порядок захвата ресурсов."
    ),
    md(
        "### Строчные и табличные блокировки\n\n"
        "Даже запрос к одной строке одновременно использует несколько механизмов. Команда берёт "
        "табличную блокировку слабого режима, чтобы таблицу нельзя было несовместимо изменить или "
        "удалить, а изменяемые строки получают row-level locks.\n\n"
        "Основные формы блокирующего чтения:\n\n"
        "- `FOR UPDATE` — строку планируется менять или удалять;\n"
        "- `FOR NO KEY UPDATE` — изменение не затрагивает ключ, на который могут ссылаться FK;\n"
        "- `FOR SHARE` — другие могут читать, но не менять строку несовместимо;\n"
        "- `FOR KEY SHARE` — самый слабый режим, защищающий ключ строки.\n\n"
        "Для большинства учебных read-modify-write сценариев нужен `FOR UPDATE`. Блокировка "
        "удерживается до конца транзакции, не до конца SELECT."
    ),
    md(
        "### Ожидание, NOWAIT и SKIP LOCKED\n\n"
        "Обычная конфликтующая команда ждёт. Это правильно для короткой транзакции, но опасно без "
        "таймаутов: пользователь видит «зависание». `NOWAIT` вместо ожидания немедленно возвращает "
        "SQLSTATE `55P03` (`lock_not_available`). `SKIP LOCKED` не сообщает ошибку, а исключает "
        "занятые строки из результата.\n\n"
        "`SKIP LOCKED` хорош для очереди задач, где любая свободная задача подходит воркеру. Он "
        "не подходит для финансового отчёта: пропуск заблокированной строки сделает результат "
        "неполным."
    ),
    md(
        "### Deadlock\n\n"
        "Deadlock — цикл ожиданий:\n\n"
        "```text\n"
        "A удерживает account 1 → ждёт account 2\n"
        "B удерживает account 2 → ждёт account 1\n"
        "```\n\n"
        "Ждать бесконечно бессмысленно, поэтому PostgreSQL обнаруживает цикл и отменяет одну "
        "транзакцию с SQLSTATE `40P01`. После ошибки нужно откатить и, если операция допускает, "
        "повторить её. Главная профилактика — единый глобальный порядок: например, всегда "
        "блокировать счета по возрастанию `account_id`."
    ),
    md(
        "### Таймауты\n\n"
        "- `lock_timeout` ограничивает ожидание блокировки;\n"
        "- `statement_timeout` ограничивает полное время команды;\n"
        "- `idle_in_transaction_session_timeout` завершает забытые бездействующие транзакции.\n\n"
        "`SET LOCAL lock_timeout = '1s'` действует только до конца текущей транзакции и безопаснее "
        "для упражнения, чем изменение параметра всей сессии."
    ),
    md(
        "## 4. SERIALIZABLE и повтор транзакции\n\n"
        "PostgreSQL реализует Serializable Snapshot Isolation. Система отслеживает зависимости "
        "чтения/записи между параллельными транзакциями. Если их совместный результат невозможно "
        "объяснить некоторым последовательным порядком, одна транзакция отменяется с SQLSTATE "
        "`40001`.\n\n"
        "Это ожидаемый механизм корректности, а не авария сервера. Retry должен:\n\n"
        "1. откатить неудачное соединение;\n"
        "2. заново начать транзакцию;\n"
        "3. повторить все чтения и вычисления;\n"
        "4. иметь ограничение попыток;\n"
        "5. желательно использовать небольшую случайную задержку.\n\n"
        "Нельзя повторять только последний UPDATE: решения могли зависеть от уже устаревших чтений."
    ),
    md(
        "### Advisory locks\n\n"
        "Advisory lock связывается не со строкой таблицы, а с числовым ключом, смысл которого "
        "задаёт приложение. Варианты `pg_advisory_xact_lock` автоматически освобождаются в конце "
        "транзакции. `pg_try_advisory_xact_lock` не ждёт и возвращает `true/false`.\n\n"
        "Такая блокировка полезна, если общей сущности нет в одной строке таблицы: например, "
        "запретить параллельную пересборку витрины за одинаковую дату. Все участники обязаны "
        "соблюдать соглашение о ключе; база сама не связывает advisory lock с данными."
    ),
    md(
        "## 5. Диагностика конкурентных проблем\n\n"
        "`pg_stat_activity` показывает сессии, их состояние, текущий запрос, начало транзакции и "
        "тип ожидания. `pg_blocking_pids(pid)` возвращает PID блокирующих сессий. `pg_locks` "
        "показывает выданные и ожидаемые блокировки, но интерпретировать его удобнее вместе с "
        "`pg_stat_activity`.\n\n"
        "Полезные признаки:\n\n"
        "- `wait_event_type = 'Lock'` — команда ждёт блокировку;\n"
        "- `state = 'idle in transaction'` — клиент оставил транзакцию открытой;\n"
        "- большой `xact_start` — транзакция длится слишком долго;\n"
        "- `pg_blocking_pids(...)` непуст — известен непосредственный блокировщик.\n\n"
        "Диагностика должна выполняться из третьей свободной сессии или отдельного подключения."
    ),
    md(
        "## 6. Как работает двухсессионный стенд\n\n"
        "В заданиях 11–30 вы заполните SQL для сессий A и B. Harness создаёт два независимых "
        "соединения, выполняет шаги в указанном порядке, задаёт таймаут и обязательно делает "
        "rollback/close. Не удаляйте команды очистки: зависшая транзакция способна блокировать "
        "последующие упражнения."
    ),
    code(
        "import json\n"
        "import psycopg2\n"
        "from concurrent.futures import ThreadPoolExecutor, TimeoutError\n"
        "DSN = 'host=sql-train-db port=5432 dbname=sql_train user=student password=sqltrain2026'\n\n"
        "def new_session():\n"
        "    connection = psycopg2.connect(DSN)\n"
        "    connection.autocommit = False\n"
        "    return connection\n\n"
        "def close_session(connection):\n"
        "    try:\n"
        "        connection.rollback()\n"
        "    finally:\n"
        "        connection.close()\n\n"
        "def save_observation(task_no, observation):\n"
        "    observation.setdefault('session_a', 'Шаги сессии A сохранены в evidence')\n"
        "    observation.setdefault('session_b', 'Шаги сессии B сохранены в evidence; для односессионного опыта не используется')\n"
        "    observation.setdefault('explanation', 'Результат рассчитан после выполнения SQL по фактическим значениям, snapshot и состоянию блокировок.')\n"
        "    with psycopg2.connect(DSN) as connection:\n"
        "        with connection.cursor() as cursor:\n"
        "            cursor.execute(\n"
        "                'SELECT training.save_tx_observation(%s, %s::jsonb)',\n"
        "                (task_no, json.dumps(observation, ensure_ascii=False)),\n"
        "            )\n\n"
        "class TxHarness:\n"
        "    \"\"\"Две PostgreSQL-сессии с журналом реально выполненных шагов.\"\"\"\n"
        "    def __init__(self):\n"
        "        self.connections = {'A': new_session(), 'B': new_session()}\n"
        "        self.executor = ThreadPoolExecutor(max_workers=2)\n"
        "        self.steps = []\n"
        "        self.futures = {}\n\n"
        "    def _execute(self, session, sql, params=None):\n"
        "        connection = self.connections[session]\n"
        "        try:\n"
        "            with connection.cursor() as cursor:\n"
        "                cursor.execute(sql, params)\n"
        "                rows = cursor.fetchall() if cursor.description else []\n"
        "            entry = {'session': session, 'sql': sql, 'rows': rows, 'sqlstate': None}\n"
        "            self.steps.append(entry)\n"
        "            return entry\n"
        "        except psycopg2.Error as error:\n"
        "            entry = {\n"
        "                'session': session,\n"
        "                'sql': sql,\n"
        "                'rows': [],\n"
        "                'sqlstate': error.pgcode,\n"
        "                'error': str(error).splitlines()[0],\n"
        "            }\n"
        "            self.steps.append(entry)\n"
        "            return entry\n\n"
        "    def run(self, session, sql, params=None):\n"
        "        \"\"\"Выполнить шаг и дождаться ответа.\"\"\"\n"
        "        return self._execute(session, sql, params)\n\n"
        "    def start(self, name, session, sql, params=None):\n"
        "        \"\"\"Запустить потенциально блокирующий шаг в фоне.\"\"\"\n"
        "        self.futures[name] = self.executor.submit(\n"
        "            self._execute, session, sql, params\n"
        "        )\n"
        "        return name\n\n"
        "    def wait(self, name, timeout=5):\n"
        "        \"\"\"Дождаться фонового шага; timeout означает, что команда пока заблокирована.\"\"\"\n"
        "        try:\n"
        "            return self.futures[name].result(timeout=timeout)\n"
        "        except TimeoutError:\n"
        "            return {'blocked': True, 'name': name, 'timeout_seconds': timeout}\n\n"
        "    def rollback(self, session):\n"
        "        self.connections[session].rollback()\n\n"
        "    def close(self):\n"
        "        for connection in self.connections.values():\n"
        "            close_session(connection)\n"
        "        self.executor.shutdown(wait=True, cancel_futures=True)\n\n"
        "    def evidence(self):\n"
        "        \"\"\"JSON-совместимый журнал без технических Python-типов.\"\"\"\n"
        "        return json.loads(json.dumps(self.steps, default=str, ensure_ascii=False))\n\n"
        "print('Двухсессионный стенд готов')"
    ),
    md(
        "### Мини-пример работы стенда\n\n"
        "Это только демонстрация механики, не решение задания. `run` ждёт ответ. `start` запускает "
        "команду в фоне — это необходимо, если она должна ждать блокировку. `wait` с коротким "
        "таймаутом позволяет доказать ожидание, не подвешивая Jupyter."
    ),
    code(
        "%%sql\n"
        "CALL training.reset_tx_lab();"
    ),
    code(
        "lab = TxHarness()\n"
        "try:\n"
        "    print(lab.run('A', 'SELECT account_id, balance FROM training.tx_accounts WHERE account_id = 1'))\n"
        "    print(lab.run('B', 'SELECT pg_backend_pid()'))\n"
        "    print(lab.evidence())\n"
        "finally:\n"
        "    lab.close()"
    ),
    md(
        "## 7. Правила выполнения\n\n"
        "1. Нарисуйте порядок шагов A/B на бумаге.\n"
        "2. Зафиксируйте ожидаемую видимость до запуска.\n"
        "3. Выполните сценарий и сохраните наблюдение.\n"
        "4. Всегда завершайте обе транзакции.\n"
        "5. Запустите автоматическую проверку.\n\n"
        "Если ячейка зависла, не запускайте её повторно: сначала остановите выполнение и сделайте "
        "`ROLLBACK` в обеих сессиях."
    ),
]

result_contracts = [
    '{"total_preserved": true, "committed": true}',
    '{"balances_restored": true, "rolled_back": true}',
    '{"savepoint_used": true, "outer_committed": true}',
    '{"commit_visible": true, "rollback_invisible": true}',
    '{"negative_balance_rejected": true}',
    '{"duplicate_prevented": true, "charged_once": true}',
    '{"balance_and_audit_atomic": true}',
    '{"constraint_deferred": true, "commit_valid": true}',
    '{"unique_conflict_recovered": true, "outer_committed": true}',
    '{"own_uncommitted_visible": true, "other_session_visible": false}',
    '{"dirty_read": false, "effective_level": "read committed"}',
    '{"non_repeatable_read": true}',
    '{"non_repeatable_read": false}',
    '{"phantom_read": true}',
    '{"phantom_read": false}',
    '{"lost_update_reproduced": true}',
    '{"lost_update_prevented": true, "method": "atomic update"}',
    '{"lost_update_prevented": true, "method": "for update"}',
    '{"second_update_waited": true}',
    '{"sqlstate": "55P03"}',
    '{"workers_selected_different_jobs": true}',
    '{"sqlstate": "40P01"}',
    '{"deadlock": false, "ordered_locking": true}',
    '{"sqlstate": "55P03", "local_timeout_used": true}',
    '{"first_lock": true, "second_lock": false}',
    '{"write_skew_reproduced": true, "invariant_broken": true}',
    '{"sqlstate": "40001", "invariant_preserved": true}',
    '{"retry_on_40001": true, "eventually_succeeded": true}',
    '{"blocker_found": true, "blocked_pid_found": true}',
    '{"total_preserved": true, "negative_balances": false}',
]

for number, (name, prompt, hint) in enumerate(tasks, 1):
    if number == 11:
        cells.append(md("## Уровень 2 — две конкурентные сессии"))
    if number == 21:
        cells.append(md("## Уровень 3 — очереди, deadlock и SERIALIZABLE"))
    cells.extend([
        md(
            f"### Задание {number}. `{name}`\n\n"
            f"**Эксперимент:** {prompt}\n\n"
            "**Что зафиксировать:** порядок команд, значения/ошибки в обеих сессиях, итоговое "
            "состояние и объяснение через snapshot или блокировку.\n\n"
            f"**Обязательный контракт `result`:** `{result_contracts[number - 1]}`. "
            "Значения должны следовать из сохранённых фактических шагов, а не из ожидания до опыта.\n\n"
            "**Частые ошибки:** autocommit остался включён, транзакция начата после первого "
            "SELECT, сессии перепутаны, блокирующая транзакция не завершена, проверяется только "
            "промежуточное, а не итоговое состояние.\n\n"
            f"<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"
        ),
        code(
            "%%sql\n"
            "-- Восстановите одинаковое начальное состояние перед новой попыткой.\n"
            "CALL training.reset_tx_lab();"
        ),
        code(
            f"# Эксперимент {number}. Команды ниже — только каркас управления сессиями.\n"
            "lab = TxHarness()\n"
            "observations = {\n"
            "    # 'session_a': 'что увидела или какую ошибку получила A',\n"
            "    # 'session_b': 'что увидела или какую ошибку получила B',\n"
            "    # 'result': 'итоговое состояние данных',\n"
            "    # 'explanation': 'объяснение через snapshot или блокировку',\n"
            "}\n"
            "try:\n"
            "    # lab.run('A', 'BEGIN ISOLATION LEVEL ...')\n"
            "    # lab.run('B', 'BEGIN ISOLATION LEVEL ...')\n"
            "    # Для ожидающей команды: lab.start('blocked_step', 'B', 'UPDATE ...')\n"
            "    # Проверка ожидания: lab.wait('blocked_step', timeout=1)\n"
            "    pass\n"
            "finally:\n"
            "    evidence = lab.evidence()\n"
            "    lab.close()\n"
            "\n"
            "# После заполнения observations сохраните также фактические шаги:\n"
            "# observations['steps'] = evidence\n"
            f"# save_observation({number}, observations)"
        ),
        code(
            "%%sql\n"
            f"SELECT * FROM training.run_checks('transactions', {number});"
        ),
        *([md("<details><summary><strong>Эталонный сценарий и разбор</strong></summary>\n\n"
             "Сначала выполните `CALL training.reset_tx_lab()`, затем создайте `lab = TxHarness()`.\n\n"
             f"```python\n{SOLUTIONS[number][0]}\n```\n\n**Что происходит:** {SOLUTIONS[number][1]}\n\n"
             "После сценария выполните `lab.close()` и запустите checker.\n\n</details>")]
          if number in SOLUTIONS else []),
    ])

cells.extend([
    md("## Прогресс"),
    code(
        "%%sql\n"
        "SELECT task_no, tests_passed, tests_total, completed, checked_at\n"
        "FROM training.progress\n"
        "WHERE module_name = 'transactions'\n"
        "ORDER BY task_no;"
    ),
])

notebook = nbf.v4.new_notebook(
    cells=cells,
    metadata={"kernelspec": {
        "display_name": "Python 3 (ipykernel)",
        "language": "python",
        "name": "python3",
    }},
)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(notebook, OUTPUT)
print(OUTPUT)
