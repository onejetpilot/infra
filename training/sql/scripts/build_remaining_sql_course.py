"""Build SQL course modules 06-12 and their structural check contracts."""
from pathlib import Path
import nbformat as nbf
from join_solutions import SOLUTIONS as JOIN_SOLUTIONS
from optimization_solutions import SOLUTIONS as OPTIMIZATION_SOLUTIONS
from etl_solutions import SOLUTIONS as ETL_SOLUTIONS
from dwh_solutions import SOLUTIONS as DWH_SOLUTIONS
from datetime_solutions import SOLUTIONS as DATETIME_SOLUTIONS
from json_arrays_solutions import SOLUTIONS as JSON_ARRAYS_SOLUTIONS
from security_solutions import SOLUTIONS as SECURITY_SOLUTIONS

ROOT = Path(__file__).resolve().parent.parent

MODULES = [
    ("01", "joins", "JOIN и гранулярность", "jn", [
        "INNER JOIN заказов и покупателей", "LEFT JOIN и отсутствующие платежи", "Антисоединение через NOT EXISTS",
        "Полусоединение через EXISTS", "Составной ключ позиции заказа", "JOIN трёх таблиц без размножения",
        "Предагрегация платежей перед JOIN", "Предагрегация позиций перед JOIN", "COUNT(*) против COUNT(column)",
        "NULL после LEFT JOIN", "Дубли ключа в справочнике", "Диагностика many-to-many",
        "Соединение по диапазону", "Неравенство в условии JOIN", "SELF JOIN покупателей одного штата",
        "LATERAL: последняя покупка клиента", "LATERAL: top-N на группу", "FULL JOIN для сверки источников",
        "UNION и UNION ALL", "INTERSECT и EXCEPT", "GROUPING SETS после соединения",
        "Платежи на уровне заказа", "Товары на уровне категории", "Продавцы на уровне штата",
        "Доставка на уровне клиента", "Среднее без ошибки average-of-averages", "Взвешенная средняя цена",
        "Контроль суммы до и после JOIN", "Контроль уникальности гранулярности", "Итоговая витрина заказа"
    ]),
    ("02", "datetime", "Даты и временные ряды", "dt", [
        "DATE, TIMESTAMP и TIMESTAMPTZ", "Приведение и date_trunc", "Извлечение компонентов даты",
        "Интервалы", "Возраст заказа", "Начало и конец месяца",
        "generate_series календаря", "Заполнение пропущенных дней", "Дневная выручка",
        "Неделя ISO", "Месячная агрегация", "Квартальная агрегация",
        "Rolling 7 calendar days", "Month-to-date", "Year-to-date",
        "Сравнение с предыдущим периодом", "Year-over-year", "Рабочие и выходные дни",
        "Праздничный календарь", "Часовые пояса", "DST и локальное время",
        "Интервалы доставки", "Просроченная доставка", "Бакеты времени",
        "Gaps and islands дат", "Последовательности активности", "Когортный месяц",
        "Retention по месяцам", "As-of snapshot", "Полная временная витрина"
    ]),
    ("04", "json_arrays", "JSONB и массивы PostgreSQL", "js", [
        "Создание JSONB", "Операторы -> и ->>", "Доступ по пути #>>",
        "Проверка существования ключа", "Containment @>", "jsonb_each",
        "jsonb_array_elements", "jsonb_to_recordset", "SQL/JSON path",
        "jsonb_set", "Удаление ключа", "Слияние объектов",
        "Агрегация jsonb_agg", "Объект jsonb_object_agg", "NULL в JSON",
        "GIN индекс jsonb_ops", "GIN jsonb_path_ops", "Expression index по JSON",
        "Создание массива", "ANY и ALL", "unnest",
        "array_agg", "Удаление дублей массива", "Пересечение массивов",
        "Многомерные массивы", "Порядок элементов WITH ORDINALITY", "JSON-схема события",
        "Валидация входного payload", "Преобразование JSON в реляционный слой", "Гибридная витрина"
    ]),
    ("09", "optimization", "Планы, индексы и оптимизация", "op", [
        "EXPLAIN и дерево плана", "EXPLAIN ANALYZE и фактические строки", "Seq Scan и Selectivity",
        "B-tree для точного равенства", "B-tree для диапазона дат", "Составной индекс",
        "Порядок колонок составного индекса", "Покрывающий индекс INCLUDE", "Partial index",
        "Expression index", "Индекс и ORDER BY LIMIT", "Index Only Scan и visibility map",
        "Bitmap Index Scan", "Функция над индексированной колонкой", "Неявное приведение типов",
        "LIKE с префиксом", "Статистика ANALYZE", "Оценка cardinality",
        "Extended statistics", "Hash Join", "Merge Join",
        "Nested Loop", "work_mem и сортировка", "CTE materialization",
        "Коррелированный подзапрос", "EXISTS вместо лишнего JOIN", "Партиционирование и pruning",
        "Блокировки при CREATE INDEX", "CREATE INDEX CONCURRENTLY", "Регрессионное сравнение планов"
    ]),
    ("10", "etl", "SQL ETL и инкрементальные загрузки", "et", [
        "Raw-to-staging типизация", "Отбраковка неверных дат", "Нормализация пустых строк",
        "Технические поля загрузки", "Контроль количества строк", "Контроль обязательных полей",
        "Контроль уникального бизнес-ключа", "INSERT только новых строк", "UPSERT через ON CONFLICT",
        "Обновление только изменившихся строк", "Идемпотентный повтор запуска", "Watermark по времени",
        "Инкремент по монотонному ключу", "Late arriving data", "Delete+insert партиции",
        "MERGE в PostgreSQL", "История запусков ETL", "Статусы и обработка ошибок",
        "Транзакционная атомарность шага", "Staging swap", "Контрольная сумма набора",
        "Сверка source-target", "Reject table", "Повторная обработка reject",
        "SCD Type 1", "SCD Type 2", "Дедупликация CDC",
        "Tombstone и логическое удаление", "Инкрементальная агрегатная витрина", "Полный перезапускаемый pipeline"
    ]),
    ("11", "dwh", "Моделирование DWH", "dw", [
        "Определение grain факта", "Бизнес-ключ и surrogate key", "Измерение клиента",
        "Измерение товара", "Измерение продавца", "Измерение даты",
        "Факт позиции заказа", "Факт платежа", "Accumulating snapshot доставки",
        "Periodic snapshot продаж", "Degenerate dimension order_id", "Junk dimension",
        "Role-playing date dimension", "Conformed dimension", "Unknown member",
        "Late arriving dimension", "SCD Type 1", "SCD Type 2",
        "Effective dating", "Текущая версия измерения", "Point-in-time JOIN",
        "Аддитивные метрики", "Полуаддитивные метрики", "Неаддитивные метрики",
        "Star schema", "Snowflake schema", "Factless fact",
        "Bridge table", "Data mart продаж", "Проверка grain и reconciliation"
    ]),
    ("12", "security", "Безопасность PostgreSQL", "sc", [
        "Роли LOGIN и NOLOGIN", "GRANT CONNECT", "USAGE на схему",
        "Права SELECT", "Права на отдельные колонки", "Роль только для чтения",
        "Роль загрузчика", "Наследование ролей", "SET ROLE",
        "PUBLIC privileges", "Default privileges", "Владелец объекта",
        "SECURITY INVOKER", "SECURITY DEFINER", "Безопасный search_path",
        "SQL injection и параметры", "Row Level Security", "RLS policy по пользователю",
        "RLS для чтения и записи", "FORCE ROW LEVEL SECURITY", "Представление как интерфейс",
        "security_barrier view", "Маскирование данных", "Аудит DDL",
        "Аудит входов", "Таймауты роли", "Ограничение temp",
        "Отзыв прав", "Матрица ролей и объектов", "Итоговая модель least privilege"
    ]),
]

THEORY = {
"joins": ["Гранулярность — что означает одна строка", "Кардинальность 1:1, 1:N и N:M", "ON определяет совпадение, WHERE фильтрует результат", "Предагрегация защищает метрики", "Контрольные суммы и уникальность"],
"optimization": ["Оптимизатор сравнивает стоимость альтернатив", "Estimated и actual rows", "Селективность и статистика", "Индекс ускоряет чтение ценой записи и места", "План измеряют на репрезентативных данных"],
"etl": ["Raw неизменяем, staging типизируем", "Идемпотентность и повторный запуск", "Watermark и опоздавшие данные", "Атомарность и журнал загрузок", "Контроли качества до публикации"],
"dwh": ["Сначала формулируется grain", "Факты содержат события и измеримые показатели", "Измерения дают контекст", "Surrogate key отделяет историю от бизнес-ключа", "Reconciliation связывает витрину с источником"],
"datetime": ["Дата не равна моменту времени", "TIMESTAMPTZ хранит абсолютный момент", "Календарная таблица делает пропуски явными", "ROWS и календарный RANGE различаются", "Границы периода задаются полуинтервалом [from,to)"],
"json_arrays": ["JSONB удобен для изменчивых атрибутов, но не отменяет модель", "-> возвращает JSON, ->> текст", "Разворачивайте массивы LATERAL", "GIN ускоряет containment", "Проверяйте форму payload на входе"],
"security": ["Права выдаются ролям, пользователи получают роли", "Минимально необходимые привилегии", "Владение сильнее обычных GRANT", "SECURITY DEFINER требует фиксированного search_path", "RLS дополняет, но не заменяет объектные права"],
}

DEEP_THEORY = {
"joins": """`JOIN` не «приклеивает колонки», а строит пары строк, удовлетворяющие `ON`. Поэтому до запроса запишите grain обеих сторон и кратность ключей. Если слева ключ уникален, а справа встречается N раз, строка слева повторится N раз. При N:M размножаются обе стороны, и `sum()` становится неверной. Безопасный шаблон: сначала агрегировать каждую деталь до требуемого grain, затем соединять.\n\n`LEFT JOIN` сохраняет строки слева; фильтр правой таблицы в `WHERE` часто случайно превращает его в INNER JOIN. Для «не существует» используйте `NOT EXISTS`, учитывая трёхзначную логику NULL. После каждого соединения сверяйте `count(*)`, `count(distinct key)` и контрольную сумму метрики. Это не отладка после работы, а часть проектирования запроса.""",
"optimization": """`EXPLAIN` показывает выбранный план, а `EXPLAIN (ANALYZE, BUFFERS)` действительно исполняет запрос и показывает время, строки, циклы и работу с буферами. Главный диагностический сигнал — расхождение estimated rows и actual rows: неверная кардинальность заставляет оптимизатор выбрать неподходящий JOIN или scan.\n\nB-tree полезен для равенства, диапазона и упорядоченного доступа, но не обязан использоваться при низкой селективности. Составной индекс подчиняется правилу ведущих колонок; `INCLUDE` может сделать чтение покрывающим; partial index хранит только строки предиката. Каждый индекс замедляет INSERT/UPDATE и занимает место. Сравнивайте планы на прогретом кэше несколько раз и оптимизируйте объём работы, а не красивое имя узла.""",
"etl": """ETL — это управляемое изменение состояния. Raw хранит исходное представление, staging выполняет безопасную типизацию и нормализацию, target публикуется только после проверок. У каждого запуска должны быть `run_id`, границы входа, время, статус, количества read/accepted/rejected/written и текст ошибки.\n\nИдемпотентность означает: повтор того же входа приводит к тому же состоянию, а не удваивает строки. Watermark выбирают по устойчивому полю и сохраняют только после успешного commit; опоздавшие события требуют overlap-окна или повторной обработки периода. UPSERT должен отличать новую запись от изменившейся. Перед публикацией сверяйте ключи, NULL, суммы и source-to-target reconciliation; при ошибке вся логическая порция откатывается.""",
"dwh": """Проектирование начинается с предложения «одна строка факта означает …». Это grain; только после него выбираются ключи измерений и метрики. Факт позиции заказа, факт платежа и факт заказа имеют разный grain и не соединяются напрямую без предагрегации. Surrogate key позволяет хранить несколько исторических версий одного business key.\n\nSCD1 перезаписывает состояние, SCD2 закрывает прежний интервал и создаёт новую версию с `[valid_from, valid_to)`. Факт должен найти версию измерения, действовавшую в момент события. Аддитивность всегда рассматривают по измерениям: остаток нельзя суммировать по времени, процент нельзя складывать вообще. Итоговая проверка — уникальность grain и сверка аддитивных показателей с источником.""",
"datetime": """`date` — календарный день, `timestamp` — локальные дата и время без зоны, `timestamptz` — абсолютный момент, отображаемый в текущей timezone. Для событий разных зон храните `timestamptz`; локальную бизнес-дату вычисляйте явно. Периоды задавайте полуинтервалом `>= start AND < next_start`, чтобы не терять дробные секунды.\n\n`date_trunc` формирует бакет, `generate_series` — календарный каркас, который делает дни без событий нулевыми строками. `ROWS 6 PRECEDING` берёт шесть строк, не шесть дней; календарное окно требует заполненного календаря или `RANGE`. Проверяйте границы месяца, високосный год, ISO-неделю, NULL и переходы DST.""",
"json_arrays": """JSONB хранит нормализованное бинарное представление и поддерживает индексацию. `->` сохраняет JSON-тип, `->>` возвращает text; неявное текстовое сравнение чисел даёт неверный порядок. Разворачивайте массив через `jsonb_array_elements`/`jsonb_to_recordset` с `LATERAL`, сразу задавая типы. Различайте отсутствующий ключ, JSON `null` и SQL NULL.\n\nGIN `jsonb_ops` поддерживает больше операторов, `jsonb_path_ops` компактнее для containment. Часто выгоднее expression index на конкретном стабильном пути. Массив PostgreSQL типизирован и подходит для небольших атомарных списков, но связь N:M обычно лучше моделировать таблицей. На входе валидируйте обязательные ключи, типы, диапазоны и допустимые значения.""",
"security": """PostgreSQL управляет доступом через роли: LOGIN разрешает вход, NOLOGIN удобно использовать как групповую роль. Для чтения таблицы нужны CONNECT к БД, USAGE к схеме и SELECT к объекту. Права будущих объектов задаёт `ALTER DEFAULT PRIVILEGES` именно от роли-создателя; существующие объекты он не меняет.\n\nВладелец может изменять объект и обходить многие ограничения, поэтому приложению не дают владение. `SECURITY DEFINER` выполняется с правами владельца и обязан иметь фиксированный безопасный `search_path`, квалифицированные имена и минимальные GRANT. RLS фильтрует строки политиками USING/WITH CHECK, но суперпользователь и обычно владелец её обходят. Проверяйте матрицу доступа через `SET ROLE`, включая явные запреты, а не только успешные сценарии.""",
}

def md(s): return nbf.v4.new_markdown_cell(s)
def code(s): return nbf.v4.new_code_cell(s)

sql_header = ["-- Generated by build_remaining_sql_course.py", "CREATE SCHEMA IF NOT EXISTS training;",
"CREATE OR REPLACE FUNCTION training.course_view_exists(p_name text) RETURNS boolean LANGUAGE sql STABLE AS $$ SELECT to_regclass('training.' || p_name) IS NOT NULL $$;",
"CREATE OR REPLACE FUNCTION training.course_view_queryable(p_name text) RETURNS boolean LANGUAGE plpgsql AS $$ BEGIN EXECUTE format('SELECT 1 FROM training.%I LIMIT 1', p_name); RETURN true; EXCEPTION WHEN OTHERS THEN RETURN false; END $$;",
"CREATE OR REPLACE FUNCTION training.course_view_has_dependencies(p_name text) RETURNS boolean LANGUAGE sql STABLE AS $$ SELECT COALESCE(EXISTS (SELECT 1 FROM pg_rewrite r JOIN pg_depend d ON d.classid='pg_rewrite'::regclass AND d.objid=r.oid AND d.deptype='n' JOIN pg_class source ON source.oid=d.refobjid JOIN pg_class answer ON answer.oid=r.ev_class JOIN pg_namespace n ON n.oid=answer.relnamespace WHERE n.nspname='training' AND answer.relname=p_name AND source.oid<>answer.oid AND source.relkind IN ('r','p','v','m')),false) $$;"]

for number, module, title, prefix, topics in MODULES:
    sql = list(sql_header)
    if module == "optimization":
        sql += [
            "CREATE TABLE IF NOT EXISTS training.op_orders AS SELECT order_id,customer_id,order_status,purchased_at,approved_at,delivered_to_customer_at FROM staging.orders;",
            "ANALYZE training.op_orders;",
        ]
    if module == "etl":
        sql += [
            "INSERT INTO training.task_tests VALUES ('etl',11,4,'Целевой ключ уникален после повтора','SELECT to_jsonb((SELECT count(*)=count(DISTINCT order_id) FROM training.etl_orders))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('etl',22,4,'Source и target согласованы по ключам','SELECT to_jsonb((SELECT missing_in_target=0 AND extra_in_target=0 FROM training.et_22))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('etl',26,4,'У SCD2 не более одной текущей версии','SELECT to_jsonb(NOT EXISTS(SELECT customer_unique_id FROM training.dim_customer_scd2 WHERE is_current GROUP BY customer_unique_id HAVING count(*)>1))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('etl',29,4,'Месячный grain уникален','SELECT to_jsonb((SELECT count(*)=count(DISTINCT month) FROM training.etl_monthly_sales))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('etl',30,4,'Последний pipeline завершился успешно','SELECT to_jsonb((SELECT status=''success'' FROM training.et_30 LIMIT 1))','SELECT ''true''::jsonb');",
        ]
    if module == "dwh":
        sql += [
            "INSERT INTO training.task_tests VALUES ('dwh',7,4,'Факт позиции покрывает источник','SELECT to_jsonb((SELECT count(*) FROM training.dw_fact_order_item)=(SELECT count(*) FROM staging.order_items))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('dwh',8,4,'Факт платежа покрывает источник','SELECT to_jsonb((SELECT count(*) FROM training.dw_fact_payment)=(SELECT count(*) FROM staging.order_payments))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('dwh',18,4,'У SCD2 одна текущая версия','SELECT to_jsonb(NOT EXISTS(SELECT customer_unique_id FROM training.dw_dim_customer_scd2 WHERE is_current GROUP BY customer_unique_id HAVING count(*)>1))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('dwh',28,4,'Bridge-веса дают единицу на заказ','SELECT to_jsonb(NOT EXISTS(SELECT order_id FROM training.dw_bridge_order_product GROUP BY order_id HAVING abs(sum(item_weight)-1)>0.000001))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('dwh',30,4,'Grain и выручка согласованы','SELECT to_jsonb((SELECT grain_valid AND reconciled FROM training.dw_30))','SELECT ''true''::jsonb');",
        ]
    if module == "etl":
        sql += [
            "CREATE TABLE IF NOT EXISTS training.etl_orders(order_id text PRIMARY KEY,customer_id text NOT NULL,order_status text,purchased_at timestamp,source_hash text,load_dttm timestamptz NOT NULL DEFAULT clock_timestamp());",
            "CREATE TABLE IF NOT EXISTS training.etl_watermark(pipeline_name text PRIMARY KEY,last_event_at timestamp,last_id text,updated_at timestamptz NOT NULL DEFAULT clock_timestamp());",
            "CREATE TABLE IF NOT EXISTS training.etl_runs(run_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,pipeline_name text,status text,rows_read bigint,rows_written bigint,rows_rejected bigint,error_message text,started_at timestamptz DEFAULT clock_timestamp(),finished_at timestamptz);",
            "CREATE TABLE IF NOT EXISTS training.etl_rejects(reject_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,source_name text,business_key text,raw_payload jsonb,reason text,rejected_at timestamptz DEFAULT clock_timestamp(),processed_at timestamptz);",
        ]
    cells = [md(f"# {title}: 30 практических заданий\n\nКурс работает на Olist в PostgreSQL. Сначала вы создаёте `training.{prefix}_01`…`training.{prefix}_30` самостоятельно, затем сверяетесь со сворачиваемым эталонным решением и запускаете тесты."),
             code("%load_ext sql\n%config SqlMagic.displaylimit = 50\n%sql postgresql+psycopg2://student:sqltrain2026@sql-train-db:5432/sql_train"),
             md("## Как работать\n\nПеред SQL письменно определите гранулярность результата, ключ, допустимые NULL и ожидаемое число строк. Сначала исследуйте данные небольшими запросами, затем создайте view. Автотест проверяет наличие и исполнимость объекта; корректность смысла дополнительно докажите контрольным запросом из условия."),
             md("## Ментальная модель\n\n" + DEEP_THEORY[module]),
             md("## Опорные понятия\n\n" + "\n\n".join(f"### {i+1}. {x}\n\nСформулируйте своими словами: что это меняет в результате, какая типичная ошибка возникает и каким контрольным запросом её обнаружить на Olist. Прежде чем писать окончательный SQL, предскажите результат на трёх вручную выбранных строках." for i,x in enumerate(THEORY[module]))),
             md("## Универсальный алгоритм\n\n1. Назовите grain одной выходной строки. 2. Назовите кандидатный ключ. 3. Опишите судьбу NULL и дублей. 4. Соберите минимальный корректный запрос. 5. Добавляйте по одному преобразованию. 6. Сверьте число строк, уникальность ключа и контрольную сумму. 7. Только после корректности оценивайте план и оформляйте view.")]
    sql.append(f"DELETE FROM training.task_tests WHERE module_name = '{module}';")
    for i, topic in enumerate(topics, 1):
        view = f"{prefix}_{i:02d}"
        level = "Базовый" if i <= 10 else "Средний" if i <= 20 else "Продвинутый"
        cells += [md(f"### Задание {i}. {topic}\n\n**Уровень:** {level}. Создайте `training.{view}` на данных `staging`/`mart`. До выполнения запишите grain и ключ. После выполнения проверьте NULL, дубли ключа и контрольную метрику.\n\n<details><summary>Подсказка</summary>\n\nНачните с минимального набора таблиц; каждый JOIN или преобразование добавляйте отдельно и сверяйте число строк.\n\n</details>"),
                  code(f"%%sql\n-- CREATE OR REPLACE VIEW training.{view} AS\n-- SELECT ...;"),
                  code(f"%%sql\n-- Контроль смысла: SELECT ... FROM training.{view};"),
                  *([md("<details><summary><strong>Эталонное решение и разбор</strong></summary>\n\n"
                       f"```sql\n{JOIN_SOLUTIONS[i][0]}\n```\n\n**Grain и действие:** {JOIN_SOLUTIONS[i][1]}\n\n"
                       "После создания VIEW сравните count(*), count(distinct key) и контрольную сумму.\n\n</details>")]
                    if module == "joins" and i in JOIN_SOLUTIONS else []),
                  *([md("<details><summary><strong>Эталонное решение и разбор</strong></summary>\n\n"
                       f"```sql\n{OPTIMIZATION_SOLUTIONS[i][0]}\n```\n\n**Что наблюдаем:** {OPTIMIZATION_SOLUTIONS[i][1]}\n\n"
                       "Выполните EXPLAIN до и после изменения, сравнивая одинаковый результат.\n\n</details>")]
                    if module == "optimization" and i in OPTIMIZATION_SOLUTIONS else []),
                  *([md("<details><summary><strong>Эталонное решение и разбор</strong></summary>\n\n"
                       f"```sql\n{ETL_SOLUTIONS[i][0]}\n```\n\n**Что делает ETL-шаг:** {ETL_SOLUTIONS[i][1]}\n\n"
                       "После запуска сравните read/accepted/rejected/written и проверьте безопасный повтор.\n\n</details>")]
                    if module == "etl" and i in ETL_SOLUTIONS else []),
                  *([md("<details><summary><strong>Эталонное решение и разбор</strong></summary>\n\n"
                       f"```sql\n{DATETIME_SOLUTIONS[i][0]}\n```\n\n**Что делает запрос:** {DATETIME_SOLUTIONS[i][1]}\n\n"
                       "Выполните решение и проверьте границы периода, NULL и отсутствие пропущенных дат.\n\n</details>")]
                    if module == "datetime" and i in DATETIME_SOLUTIONS else []),
                  *([md("<details><summary><strong>Эталонное решение и разбор</strong></summary>\n\n"
                       f"```sql\n{JSON_ARRAYS_SOLUTIONS[i][0]}\n```\n\n**Что делает запрос:** {JSON_ARRAYS_SOLUTIONS[i][1]}\n\n"
                       "Проверьте тип результата, различие SQL NULL/JSON null и число строк после разворачивания.\n\n</details>")]
                    if module == "json_arrays" and i in JSON_ARRAYS_SOLUTIONS else []),
                  *([md("<details><summary><strong>Эталонное решение и разбор</strong></summary>\n\n"
                       f"```sql\n{SECURITY_SOLUTIONS[i][0]}\n```\n\n**Модель доступа:** {SECURITY_SOLUTIONS[i][1]}\n\n"
                       "Проверяйте не только разрешённую операцию, но и ожидаемый отказ лишней операции.\n\n</details>")]
                    if module == "security" and i in SECURITY_SOLUTIONS else []),
                  *([md("<details><summary><strong>Эталонное решение и разбор</strong></summary>\n\n"
                       f"```sql\n{DWH_SOLUTIONS[i][0]}\n```\n\n**Модель и grain:** {DWH_SOLUTIONS[i][1]}\n\n"
                       "После загрузки проверьте уникальность grain, orphan keys и reconciliation метрик.\n\n</details>")]
                    if module == "dwh" and i in DWH_SOLUTIONS else []),
                  code(f"%%sql\nSELECT * FROM training.run_checks('{module}', {i});")]
        sql += [f"INSERT INTO training.task_tests VALUES ('{module}',{i},1,'Представление training.{view} создано','SELECT to_jsonb(training.course_view_exists(''{view}''))','SELECT ''true''::jsonb');",
                f"INSERT INTO training.task_tests VALUES ('{module}',{i},2,'Представление выполняется без ошибки','SELECT to_jsonb(training.course_view_queryable(''{view}''))','SELECT ''true''::jsonb');",
                f"INSERT INTO training.task_tests VALUES ('{module}',{i},3,'Решение использует объекты базы, а не константный SELECT','SELECT to_jsonb(training.course_view_has_dependencies(''{view}''))','SELECT ''true''::jsonb');"]
    if module == "joins":
        sql += [
            "INSERT INTO training.task_tests VALUES ('joins',1,4,'INNER JOIN сохраняет все заказы','SELECT to_jsonb((SELECT count(*) FROM training.jn_01)=(SELECT count(*) FROM staging.orders))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('joins',7,4,'Предагрегация сохраняет grain заказа','SELECT to_jsonb((SELECT count(*)=count(DISTINCT order_id) FROM training.jn_07))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('joins',18,4,'FULL JOIN сохраняет уникальный order_id','SELECT to_jsonb((SELECT count(*)=count(DISTINCT order_id) FROM training.jn_18))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('joins',28,4,'Контрольные суммы совпали','SELECT to_jsonb((SELECT totals_match FROM training.jn_28))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('joins',29,4,'Заявленный grain уникален','SELECT to_jsonb((SELECT grain_is_unique FROM training.jn_29))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('joins',30,4,'Итоговая витрина имеет одну строку заказа','SELECT to_jsonb((SELECT count(*)=count(DISTINCT order_id) FROM training.jn_30))','SELECT ''true''::jsonb');",
        ]
    if module == "datetime":
        sql += [
            "INSERT INTO training.task_tests VALUES ('datetime',7,4,'Календарь не содержит пропусков','SELECT to_jsonb(NOT EXISTS(SELECT 1 FROM training.dt_07 a LEFT JOIN training.dt_07 b ON b.calendar_date=a.calendar_date+1 WHERE a.calendar_date<(SELECT max(calendar_date) FROM training.dt_07) AND b.calendar_date IS NULL))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('datetime',8,4,'Заполнены все календарные дни','SELECT to_jsonb((SELECT count(*)=max(day)-min(day)+1 FROM training.dt_08))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('datetime',13,4,'Rolling-витрина имеет уникальный день','SELECT to_jsonb((SELECT count(*)=count(DISTINCT day) FROM training.dt_13))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('datetime',28,4,'Retention находится между нулём и единицей','SELECT to_jsonb(NOT EXISTS(SELECT 1 FROM training.dt_28 WHERE retention_rate<0 OR retention_rate>1))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('datetime',30,4,'Итоговая витрина не теряет дни','SELECT to_jsonb((SELECT count(*)=max(day)-min(day)+1 FROM training.dt_30))','SELECT ''true''::jsonb');",
        ]
    if module == "json_arrays":
        sql += [
            "INSERT INTO training.task_tests VALUES ('json_arrays',7,4,'Разворачивание вернуло все платежи','SELECT to_jsonb((SELECT count(*) FROM training.js_07)=(SELECT count(*) FROM staging.order_payments))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('json_arrays',13,4,'JSON-массив создан для каждого заказа с позициями','SELECT to_jsonb(NOT EXISTS(SELECT 1 FROM training.js_13 WHERE jsonb_typeof(items)<>''array''))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('json_arrays',16,4,'GIN jsonb_ops создан','SELECT to_jsonb(EXISTS(SELECT 1 FROM pg_indexes WHERE schemaname=''training'' AND tablename=''js_documents'' AND indexdef ILIKE ''%using gin%''))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('json_arrays',28,4,'Все сгенерированные события валидны','SELECT to_jsonb(NOT EXISTS(SELECT 1 FROM training.js_28 WHERE NOT is_valid))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('json_arrays',30,4,'Гибридная витрина сохраняет grain заказа','SELECT to_jsonb((SELECT count(*)=count(DISTINCT order_id) FROM training.js_30))','SELECT ''true''::jsonb');",
        ]
    if module == "security":
        sql += [
            "INSERT INTO training.task_tests VALUES ('security',6,4,'Readonly-роль не может изменять staging.orders','SELECT to_jsonb(NOT has_table_privilege(''training_readonly'',''staging.orders'',''INSERT''))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('security',10,4,'PUBLIC не может создавать объекты в public','SELECT to_jsonb(NOT has_schema_privilege(''public'',''public'',''CREATE''))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('security',15,4,'У definer-функции зафиксирован search_path','SELECT to_jsonb((SELECT proconfig IS NOT NULL FROM pg_proc WHERE oid=''training.sc_safe_count()''::regprocedure))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('security',20,4,'RLS принудительно применяется к владельцу','SELECT to_jsonb((SELECT relforcerowsecurity FROM pg_class WHERE oid=''training.sc_user_rows''::regclass))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('security',30,4,'Итоговый пользователь получил read и write роли','SELECT to_jsonb((SELECT count(*)=2 FROM training.sc_30))','SELECT ''true''::jsonb');",
        ]
    if module == "optimization":
        sql += [
            "INSERT INTO training.task_tests VALUES ('optimization',4,4,'B-tree по order_id создан','SELECT to_jsonb(EXISTS(SELECT 1 FROM pg_indexes WHERE schemaname=''training'' AND tablename=''op_orders'' AND indexdef LIKE ''%(order_id)%''))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('optimization',17,4,'Статистика таблицы доступна','SELECT to_jsonb(EXISTS(SELECT 1 FROM pg_stats WHERE schemaname=''training'' AND tablename=''op_orders''))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('optimization',19,4,'Extended statistics создана','SELECT to_jsonb(EXISTS(SELECT 1 FROM pg_stats_ext WHERE schemaname=''training'' AND statistics_name=''st_op_status_date''))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('optimization',27,4,'Создана partitioned-таблица с дочерними партициями','SELECT to_jsonb((SELECT count(*)>=3 FROM pg_inherits WHERE inhparent=''training.op_orders_part''::regclass))','SELECT ''true''::jsonb');",
            "INSERT INTO training.task_tests VALUES ('optimization',29,4,'Индекс даты доставки создан','SELECT to_jsonb(EXISTS(SELECT 1 FROM pg_indexes WHERE schemaname=''training'' AND tablename=''op_orders'' AND indexname LIKE ''%delivered_at%''))','SELECT ''true''::jsonb');",
        ]
    cells += [md("## Прогресс"), code(f"%%sql\nSELECT * FROM training.progress WHERE module_name='{module}' ORDER BY task_no;")]
    nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec":{"display_name":"Python 3 (ipykernel)","language":"python","name":"python3"}})
    nbf.write(nb, ROOT / "notebooks" / f"{number}_{title.replace(' ', '_').replace('/', '_')}_30_Tasks.ipynb")
    (ROOT / "sql" / f"{int(number)*10:03d}_{module}_tests.sql").write_text("\n".join(sql) + "\n", encoding="utf-8")

all_modules = [
    ("01", "JOIN_и_гранулярность", "JOIN и гранулярность"),
    ("02", "Даты_и_временные_ряды", "Даты и временные ряды"),
    ("03", "Window_Functions", "Оконные функции"),
    ("04", "JSONB_и_массивы_PostgreSQL", "JSONB и массивы PostgreSQL"),
    ("05", "Functions", "Функции PostgreSQL"),
    ("06", "Procedures", "Процедуры и управляемые изменения"),
    ("07", "Transactions_Isolation", "Транзакции, изоляция и блокировки"),
    ("08", "Deduplication", "Дедупликация и качество"),
    ("09", "Планы,_индексы_и_оптимизация", "Планы, индексы и оптимизация"),
    ("10", "SQL_ETL_и_инкрементальные_загрузки", "SQL ETL и инкрементальные загрузки"),
    ("11", "Моделирование_DWH", "Моделирование DWH"),
    ("12", "Безопасность_PostgreSQL", "Безопасность PostgreSQL"),
]
map_cells = [
    md("# SQL Course Map\n\nПолная траектория из 12 модулей и 360 практических заданий на PostgreSQL/Olist. После рабочей ячейки находится сворачиваемое эталонное решение с разбором; прогресс фиксирует `training.run_checks`."),
    code("%load_ext sql\n%sql postgresql+psycopg2://student:sqltrain2026@sql-train-db:5432/sql_train"),
    md("## Порядок прохождения\n\n" + "\n".join(f"{i}. **{title}** — `training/{num}`" for i, (num, _, title) in enumerate(all_modules, 1))),
    md("## Схема данных Olist\n\n```text\ncustomers 1 ── N orders 1 ── N order_items N ── 1 products\n                       │              │\n                       │              └── N:1 sellers\n                       ├── 1:N order_payments\n                       └── 1:N order_reviews\nproducts N ── 1 product_category_translation\ncustomers/sellers N ── 1 geolocation (по zip_code_prefix после агрегации)\n```\n\nРабочие типизированные объекты находятся в `staging`. `order_id` — ключ заказа; `(order_id, order_item_id)` — grain позиции; у платежей grain `(order_id, payment_sequence)`. Перед JOIN всегда проверяйте фактическую уникальность, а не полагайтесь только на рисунок."),
    md("## Рекомендуемый ритм\n\nПроходите задания по порядку: теория → прогноз результата → SQL → контрольные запросы → автотест. После каждых 10 заданий объясните вслух grain, NULL-семантику и причину выбранной конструкции. Не переходите к следующему модулю с непонятым FAIL."),
    code("%%sql\nSELECT module_name, count(*) AS attempted, count(*) FILTER (WHERE completed) AS completed\nFROM training.progress\nGROUP BY module_name ORDER BY module_name;")
]
nbf.write(nbf.v4.new_notebook(cells=map_cells, metadata={"kernelspec":{"display_name":"Python 3 (ipykernel)","language":"python","name":"python3"}}), ROOT / "notebooks" / "00_SQL_Course_Map.ipynb")

# Репозиторий содержит чистые учебные шаблоны: результаты выполнения остаются только
# в пользовательской рабочей копии Jupyter и не превращаются в скрытые ответы.
for notebook_path in (ROOT / "notebooks").glob("*.ipynb"):
    notebook = nbf.read(notebook_path, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    nbf.write(notebook, notebook_path)

print("Built", len(MODULES), "modules")
