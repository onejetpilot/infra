"""Add deep teaching layers to generated SQL notebooks without publishing solutions."""
from pathlib import Path
import nbformat as nbf
R=Path(__file__).resolve().parent.parent

MODULES={
'01_Functions_30_Tasks.ipynb':('Функции PostgreSQL','Функция превращает входные значения в результат и участвует в выражении SQL. Важны не только тело, но контракт типов, NULL, volatility, безопасность search_path и стоимость многократного вызова.','raw/staging Olist и training.function_audit','Сначала сформулируйте сигнатуру и поведение на NULL/границах; затем отделите вычисление от побочных эффектов и проверьте несколько классов входа.'),
'02_Procedures_30_Tasks.ipynb':('Процедуры','Процедура — команда изменения состояния. В отличие от функции она вызывается CALL и проектируется вокруг атомарности, повторного запуска, журнала и понятного результата.','training-песочница, staging Olist','Опишите состояние до и после, инвариант, границу транзакции и реакцию на повтор. Только затем пишите DML.'),
'03_Deduplication_30_Tasks.ipynb':('Дедупликация','Дубликат определяется бизнес-смыслом, а не совпадением всей строки. Нужны business key, правило канонической версии, tie-breaker, аудит удалённого и защита от повторного появления.','копии сущностей Olist в training','Профилируйте ключ, классифицируйте exact/semantic/version duplicates, ранжируйте детерминированно и сначала публикуйте кандидатов на удаление.'),
'04_Transactions_Isolation_30_Tasks.ipynb':('Транзакции и изоляция','MVCC даёт каждой команде или транзакции snapshot, а блокировки координируют конфликтующие записи. Уровень изоляции определяет допустимые изменения видимости, но инварианты всё равно нужно проектировать.','training.tx_accounts, operations, jobs, doctors','Нарисуйте timeline A/B, зафиксируйте точки BEGIN/SELECT/UPDATE/COMMIT, предскажите snapshot и ожидание блокировки, затем сравните фактический SQLSTATE.'),
'05_Window_Functions_30_Tasks.ipynb':('Оконные функции','Окно считает по связанным строкам, сохраняя grain результата. PARTITION BY задаёт независимые группы, ORDER BY — последовательность, frame — видимый диапазон.','mart.order_finance, customer_summary, product_sales','Сначала определите grain, затем partition, детерминированный order и frame. Фильтруйте вычисленное окно на внешнем уровне.'),
'06_JOIN_и_гранулярность_30_Tasks.ipynb':('JOIN и гранулярность','JOIN строит пары строк. Кратность ключей определяет число результата; N:M незаметно умножает метрики. LEFT JOIN легко случайно превратить в INNER фильтром справа.','staging.orders/items/payments/customers/products','Запишите grain обеих сторон и ожидаемую кратность. Предагрегируйте детали, добавляйте JOIN по одному и сверяйте count/distinct/sum.'),
'07_Планы,_индексы_и_оптимизация_30_Tasks.ipynb':('Планы и индексы','Оптимизатор выбирает физический способ получить тот же результат по статистике и стоимости. Индекс — дополнительная структура с ценой записи и места, а не универсальный ускоритель.','Olist staging/mart и pg_catalog','Сначала докажите корректность, затем снимите EXPLAIN ANALYZE BUFFERS, найдите главное расхождение estimated/actual и уменьшите объём работы.'),
'08_SQL_ETL_и_инкрементальные_загрузки_30_Tasks.ipynb':('SQL ETL','ETL управляет изменением состояния: raw неизменяем, staging типизирует, target публикуется после quality gate. Run metadata и reconciliation являются частью результата.','raw → staging → mart Olist','Определите batch boundary, idempotency key, accepted/rejected и формулу reconciliation. Watermark меняйте только после успешной публикации.'),
'09_Моделирование_DWH_30_Tasks.ipynb':('Моделирование DWH','Проектирование факта начинается с предложения «одна строка означает…». Измерения дают контекст, surrogate key связывает факт с исторической версией business entity.','Olist orders/items/payments как источники фактов','Зафиксируйте grain, измерения, degenerate keys и аддитивность каждой метрики; после загрузки докажите uniqueness и reconciliation.'),
'10_Даты_и_временные_ряды_30_Tasks.ipynb':('Даты и временные ряды','DATE, TIMESTAMP и TIMESTAMPTZ отвечают на разные вопросы. Календарный каркас делает пропущенные периоды явными, а полуинтервал [start,next_start) защищает границы.','timestamps заказов и доставки Olist','Уточните timezone и бизнес-дату, создайте календарь, агрегируйте до периода, заполните пропуски и только затем считайте динамику.'),
'11_JSONB_и_массивы_PostgreSQL_30_Tasks.ipynb':('JSONB и массивы','JSONB полезен для изменчивого payload, но отсутствующий ключ, JSON null и SQL NULL различаются. GIN и expression index оптимизируют разные шаблоны доступа.','учебные payload и атрибуты Olist','Опишите JSON contract, проверьте типы/обязательные пути, разверните множества LATERAL и сравнивайте числа после явного cast.'),
'12_Безопасность_PostgreSQL_30_Tasks.ipynb':('Безопасность PostgreSQL','Доступ складывается из CONNECT, USAGE, object privileges, membership, ownership и RLS. Проверять нужно и разрешённые, и запрещённые сценарии через SET ROLE.','training schema, роли и pg_catalog','Постройте матрицу role×object×operation, выдайте минимум прав, зафиксируйте search_path SECURITY DEFINER и докажите отказ лишнего доступа.')}

NEW_NAMES = {
    '01_Functions_30_Tasks.ipynb': '05_Functions_30_Tasks.ipynb',
    '02_Procedures_30_Tasks.ipynb': '06_Procedures_30_Tasks.ipynb',
    '03_Deduplication_30_Tasks.ipynb': '08_Deduplication_30_Tasks.ipynb',
    '04_Transactions_Isolation_30_Tasks.ipynb': '07_Transactions_Isolation_30_Tasks.ipynb',
    '05_Window_Functions_30_Tasks.ipynb': '03_Window_Functions_30_Tasks.ipynb',
    '06_JOIN_и_гранулярность_30_Tasks.ipynb': '01_JOIN_и_гранулярность_30_Tasks.ipynb',
    '07_Планы,_индексы_и_оптимизация_30_Tasks.ipynb': '09_Планы,_индексы_и_оптимизация_30_Tasks.ipynb',
    '08_SQL_ETL_и_инкрементальные_загрузки_30_Tasks.ipynb': '10_SQL_ETL_и_инкрементальные_загрузки_30_Tasks.ipynb',
    '09_Моделирование_DWH_30_Tasks.ipynb': '11_Моделирование_DWH_30_Tasks.ipynb',
    '10_Даты_и_временные_ряды_30_Tasks.ipynb': '02_Даты_и_временные_ряды_30_Tasks.ipynb',
    '11_JSONB_и_массивы_PostgreSQL_30_Tasks.ipynb': '04_JSONB_и_массивы_PostgreSQL_30_Tasks.ipynb',
}
MODULES = {NEW_NAMES.get(name, name): value for name, value in MODULES.items()}

ER='''```text
customers 1 ── N orders 1 ── N order_items N ── 1 products
                       │              └──────── N:1 sellers
                       ├── 1:N order_payments
                       └── 1:N order_reviews
```
`orders` имеет grain заказа, `order_items` — позиции, `order_payments` — части оплаты.
Соединять две детали без предварительной агрегации опасно: 3 позиции × 2 платежа = 6 строк.'''

def md(x):return nbf.v4.new_markdown_cell(x)
for path in sorted((R/'notebooks').glob('*.ipynb')):
    if path.name not in MODULES: continue
    nb=nbf.read(path,as_version=4); title,model,data,method=MODULES[path.name]
    # Remove previous enhancer cells to keep reruns idempotent.
    nb.cells=[c for c in nb.cells if c.metadata.get('theory_enhancer')!='sql-v1']
    extra=[
      md(f'''## Результаты обучения

После модуля **{title}** вы должны уметь объяснить механизм своими словами, выбрать
конструкцию по требованиям, предсказать поведение на NULL/дубликатах/границах,
доказать grain и ключ результата и расшифровать причину PASS/FAIL автоматической проверки.

Предварительно нужно понимать SELECT, типы PostgreSQL и схему Olist.'''),
      md(f'''## Ментальная модель

{model}

Главный вопрос не «какой синтаксис вспомнить», а «какое состояние или множество строк
должно получиться и какой механизм PostgreSQL это гарантирует».'''),
      md(f'''## Данные модуля

Основные объекты: `{data}`.

{ER}

Полное описание колонок находится в `data-catalog/00_Data_Catalog_and_Schemas.ipynb`.'''),
      md(f'''## Алгоритм решения

1. Сформулируйте смысл одной выходной строки.
2. Назовите candidate key и допустимые NULL.
3. Предскажите число строк и контрольную метрику.
4. Соберите минимальный корректный запрос.
5. Добавляйте по одному преобразованию и проверяйте промежуточный результат.
6. Проверьте пустой набор, одну строку, ничью/дубликат и NULL.
7. Создайте требуемый объект и запустите checker.

Специально для этого модуля: {method}'''),
      md('''## Типичные ошибки

- Начать с длинного запроса без grain и ключа.
- Скрыть дубликаты `DISTINCT`, не найдя причину.
- Считать NULL обычным значением.
- Проверить только несколько красивых строк вместо инварианта.
- Оптимизировать физический план до доказательства логической корректности.
- Подогнать имя объекта под checker, не выполнив смысл задания.'''),
      md('''## Самопроверка перед практикой

1. Чем бизнес-ключ отличается от surrogate key?
2. Как доказать, что JOIN не размножил метрику?
3. Что произойдёт на пустом наборе и на NULL?
4. Какая проверка должна остаться истинной после повторного запуска?
5. Как независимым запросом опровергнуть собственное решение?''')]
    for c in extra:c.metadata['theory_enhancer']='sql-v1'
    nb.cells[1:1]=extra
    for c in nb.cells:
      if c.cell_type=='markdown' and c.source.startswith('### Задание ') and '<!-- task-card-sql-v1 -->' not in c.source:
        c.source += '''

<!-- task-card-sql-v1 -->
#### Как подойти к заданию

- **Учебная цель:** объясните, какой механизм текущего модуля здесь проверяется.
- **Входной grain:** определите его по каталогу данных, не по названию таблицы.
- **Целевой grain:** запишите одним предложением до SQL.
- **Контракт результата:** требуемый объект, ключ, колонки, допустимые NULL и инвариант.
- **Порядок:** профиль входа → минимальный SELECT → граничные случаи → объект → checker.
- **Самопроверка:** `count(*)`, `count(distinct key)`, NULL и контрольная сумма/состояние.
- **Checker:** проверяет формальный и содержательный контракт; PASS не заменяет объяснение.

Частая ошибка — сразу копировать знакомый шаблон, не проверив его grain, порядок строк или
поведение при повторе. Готового решения в подсказке намеренно нет.'''
    for c in nb.cells:
      if c.cell_type=='code': c.outputs=[];c.execution_count=None
    nbf.write(nb,path)
