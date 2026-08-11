import os
from pathlib import Path
import nbformat as nbf
from distribution_solutions import SOLUTIONS

ROOT=Path(__file__).resolve().parent.parent
OUTPUT=Path(os.environ.get("GREENPLUM_DISTRIBUTION_OUTPUT",ROOT/"notebooks"/"01_Distribution_30_Tasks.ipynb"))

tasks=[
("gpd_01_segment_rows","Исследуйте фактическое размещение всех 100000 строк `greenplum_training.dist_source` на четырёх primary-сегментах и сохраните результат в VIEW с колонками `segment_id`, `rows_count`.","Физический сегмент определяется системным полем `gp_segment_id`; обычной колонки `segment_id` в источнике нет."),
("gpd_02_random","Создайте таблицу-копию источника `DISTRIBUTED RANDOMLY`.","CTAS поддерживает предложение распределения."),
("gpd_03_by_event","Создайте копию `DISTRIBUTED BY (event_id)`.","Уникальный равномерный ключ — базовый вариант."),
("gpd_04_by_country","Создайте копию `DISTRIBUTED BY (country)`.","Низкая кардинальность может дать перекос."),
("gpd_05_by_hot_key","Создайте копию `DISTRIBUTED BY (hot_key)`.","Источник специально содержит одно очень частое значение."),
("gpd_06_distribution","Создайте VIEW segment_id, rows_count для таблицы gpd_05_by_hot_key.","Сравните максимум и среднее."),
("gpd_07_skew_ratio","Создайте VIEW с одной колонкой skew_ratio = max(rows)/avg(rows), округление 4 знака.","Не теряйте сегменты с нулём строк."),
("gpd_08_skew_coefficient","Создайте VIEW с `skew_coefficient` в процентах для gpd_05.","Используйте стандартное отклонение относительно среднего."),
("gpd_09_null_key","Создайте таблицу по nullable_key и исследуйте размещение NULL.","NULL тоже участвует в хешировании."),
("gpd_10_composite","Создайте копию `DISTRIBUTED BY (country, user_id)`.","Составной ключ может компенсировать слабую первую колонку."),
("gpd_11_replicated_dim","Создайте `m_razhin.gpd_11_replicated_dim` из справочника стран с replicated policy.","Репликация подходит только малым справочникам."),
("gpd_12_dim_hash","Создайте тот же справочник `DISTRIBUTED BY (country_code)`.","Он понадобится для сравнения планов."),
("gpd_13_fact_country","Создайте fact-копию, распределённую по country.","Ключ должен совпасть с ключом JOIN."),
("gpd_14_colocated_join","Создайте VIEW результата JOIN gpd_13_fact_country и hash-справочника по стране.","Физические типы и distribution keys должны совпадать."),
("gpd_15_replicated_join","Создайте VIEW JOIN факта с replicated-справочником.","Реплицированный набор локален на каждом сегменте."),
("gpd_16_motion_plan","Сохраните в VIEW количество Motion-строк плана несовместимого JOIN.","Используйте EXPLAIN через учебную функцию."),
("gpd_17_colocated_plan","Сохраните количество Motion для colocated JOIN.","Сравните с предыдущим заданием."),
("gpd_18_random_join","Создайте random fact и измерьте Motion при JOIN.","Random policy не гарантирует colocated строки."),
("gpd_19_group_motion","Измерьте Motion для GROUP BY country на таблице, распределённой по event_id.","Агрегат по чужому ключу требует обмена."),
("gpd_20_local_group","Измерьте Motion для GROUP BY country на таблице, распределённой по country.","Часть агрегации может быть локальной."),
("gpd_21_filter_skew","Покажите распределение строк после фильтра `country='RU'`.","Даже ровная таблица может дать runtime skew после фильтра."),
("gpd_22_join_skew","Покажите распределение результата JOIN по hot_key.","Skew бывает не только у хранения, но и у операции."),
("gpd_23_size_by_segment","Создайте VIEW размера gpd_05 на каждом сегменте.","Используйте `pg_relation_size` на сегментах."),
("gpd_24_rows_vs_bytes","Создайте VIEW, сравнивающее долю строк и долю байтов сегмента.","Одинаковое число строк не гарантирует одинаковый объём."),
("gpd_25_metrica_profile","Создайте профиль кардинальности date, regioncountry, regioncity, ipaddress источника Метрики.","Верните количество строк и distinct для каждого кандидата."),
("gpd_26_metrica_candidate","Создайте учебную выборку Метрики с выбранным ключом распределения.","Не изменяйте исходную внешнюю таблицу."),
("gpd_27_metrica_skew","Рассчитайте распределение и skew_ratio созданной выборки.","Обоснуйте ключ в markdown перед SQL."),
("gpd_28_query_motion","Проверьте Motion для типового фильтра Метрики из задания.","Фильтр сам по себе не обязан создавать Motion."),
("gpd_29_redistribute","Создайте новую копию источника с улучшенной policy относительно gpd_05.","CTAS безопаснее учебного изменения исходника."),
("gpd_30_recommendation","Создайте VIEW-рекомендацию: table_name, policy, skew_ratio, motion_count, verdict для трёх вариантов.","Итог должен опираться на измерения."),
]
def md(x): return nbf.v4.new_markdown_cell(x)
def code(x): return nbf.v4.new_code_cell(x)
cells=[
md("# Распределение данных Greenplum — 30 заданий\n\nРаспределение определяет, на каком primary-сегменте хранится строка. В модуле используются учебные копии в `m_razhin` и источник `greenplum_training.dist_source`. Сначала выполните задание самостоятельно, затем раскройте эталонное решение."),
code("%load_ext sql\n%config SqlMagic.displaylimit = 100\n%sql postgresql+psycopg2://gpadmin@cbdb-coordinator:5432/moex"),
md("""## Учебный источник `greenplum_training.dist_source`

Одна строка — синтетическое событие. Источник содержит ровно **100000 строк** и физически
распределён по `event_id`. Он специально включает хорошие и плохие кандидаты на ключ.

| Колонка | Тип | Смысл | Зачем в модуле |
|---|---|---|---|
|`event_id`|bigint|уникальный ID события|высокая cardinality и равномерный hash|
|`event_date`|date|день в диапазоне 90 дней|пример фильтра/partition-кандидата|
|`user_id`|bigint|один из 20000 пользователей|повторяющийся JOIN/GROUP key|
|`country`|text|одна из 8 стран|низкая cardinality, полезный JOIN key|
|`city`|text|один из 200 городов|средняя cardinality|
|`hot_key`|text|`HOT` у 80000 строк|намеренно сильный data skew|
|`nullable_key`|integer|каждая пятая строка NULL|влияние NULL на distribution|
|`payload`|text|строки разной длины|различие row skew и byte skew|

### Системное поле `gp_segment_id`

`gp_segment_id` не входит в DDL таблицы. Greenplum предоставляет его при чтении как
идентификатор сегмента, на котором физически находится строка. Поэтому:

- `segment_id` использовать нельзя — такой колонки нет;
- `gp_segment_id` можно выбрать и переименовать в `segment_id` в результате;
- `GROUP BY gp_segment_id` показывает количество строк на каждом непустом сегменте;
- в этом источнике ожидаются четыре группы, потому что кластер имеет четыре primary content.

Посмотреть схему до решения:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'greenplum_training'
  AND table_name = 'dist_source'
ORDER BY ordinal_position;
```
"""),
md("## 1. Физическая модель\n\nCoordinator не хранит пользовательские строки. Для hash distribution Greenplum вычисляет хеш ключа и выбирает content. `DISTRIBUTED RANDOMLY` распределяет без бизнес-ключа. `DISTRIBUTED REPLICATED` хранит полный набор на каждом primary и подходит только маленьким измерениям."),
md("### Hash distribution\n\nДля строки Greenplum хеширует distribution columns и сопоставляет результат одному content. Одинаковый ключ всегда попадает на один логический сегмент — это основа colocated JOIN. Хеш-функция не может исправить частоты: если 80% строк имеют один hot key, они окажутся вместе."),
md("### Random policy\n\n`DISTRIBUTED RANDOMLY` не связывает размещение с бизнес-колонкой и часто даёт приемлемый баланс массовой загрузки. Однако две random-таблицы не colocated: одинаковые JOIN-ключи могут находиться на разных сегментах, поэтому запросу потребуется Motion."),
md("### Replicated policy\n\nПолный справочник хранится на каждом primary. Большой факт соединяется с ним локально без пересылки. Цена — умножение места и работы загрузки на число сегментов. Репликация предназначена для небольших, относительно стабильных измерений, а не фактов."),
md("## 2. Как выбирать ключ\n\nХороший ключ одновременно имеет высокую кардинальность, равномерную частоту, мало NULL, стабилен и совпадает с ключами крупных JOIN. Уникальный ключ часто равномерен, но не всегда оптимален для JOIN. Низкая кардинальность и hot key создают skew."),
md("### Кардинальность и частота\n\n`count(distinct key)` недостаточно. Профиль кандидата включает число строк, distinct, NULL, максимальную частоту и долю top-значения. Два ключа одинаковой кардинальности могут иметь совершенно разный skew."),
md("### Составной ключ\n\nКомбинация `(a,b)` повышает разнообразие, если `a` слабый. Но colocated JOIN потребует соединения по совместимой комбинации. Добавленная ради баланса колонка может устранить skew хранения и одновременно ухудшить главный JOIN."),
md("### NULL\n\nNULL участвует в distribution policy. Большое число NULL в единственной колонке ведёт себя как hot key. Перед выбором policy обязательно измеряйте NULL rate."),
md("## 3. Skew\n\nСравнивайте строки и байты каждого сегмента. `max/avg` легко интерпретировать: 1 — идеальный баланс. Коэффициент вариации `100*stddev/avg` удобен для сравнения таблиц. Обязательно учитывайте сегменты с нулём строк."),
md("### Метрики\n\nДля counts `n_i` используют `max/avg`, размах `(max-min)/avg` и коэффициент вариации `100*stddev_pop/avg`. Идеальные значения — 1 и 0%. Универсального допустимого порога нет: важны объём и влияние на реальные запросы."),
md("### Нулевые сегменты\n\n`GROUP BY gp_segment_id` не показывает пустой content. Корректная диагностика начинает со списка четырёх primary content и делает LEFT JOIN к counts, иначе экстремальный skew будет недооценён."),
md("### Строки и байты\n\nСтроки могут иметь разный размер из-за text, JSON и массивов. Ровные counts не гарантируют одинаковый I/O. Поэтому сравнивают и `pg_relation_size` на сегментах."),
code("%%sql\nSELECT gp_segment_id,count(*) rows_count\nFROM greenplum_training.dist_source\nGROUP BY gp_segment_id ORDER BY 1;"),
md("## 4. Motion\n\n`Redistribute Motion` пересылает строки по новому хешу; `Broadcast Motion` копирует небольшой набор; `Gather Motion` собирает результат. Colocated JOIN возможен, когда обе большие таблицы распределены совместимо по ключу соединения. Replicated dimension также устраняет пересылку факта."),
md("### Redistribute\n\nСтрока получает новый destination content и может уйти по interconnect. Это требуется для JOIN, DISTINCT или GROUP BY по несовместимому ключу. Стоимость зависит от количества и ширины строк после ранних фильтров."),
md("### Broadcast\n\nНебольшой набор копируется каждому принимающему сегменту, а большой остаётся на месте. Ошибочная статистика может заставить optimizer broadcast-ить слишком большой набор."),
md("### Gather\n\nРезультат собирается одному получателю. Небольшой финальный Gather нормален; ранний Gather большого набора уничтожает параллелизм."),
md("### Colocation\n\nНужны совместимые типы, одинаковое число distribution columns и JOIN по всем ключам. Одинакового имени колонки недостаточно. Выражение или cast над ключом также может потребовать Motion."),
md("### Чтение EXPLAIN\n\nЧитайте снизу вверх. Для каждого Motion спросите: какой набор движется, почему текущая policy не подходит, можно ли уменьшить строки раньше и достаточно ли част запрос, чтобы менять физическую модель."),
code("%%sql\nEXPLAIN SELECT *\nFROM greenplum_training.dist_source a\nJOIN greenplum_training.dist_dimension b USING(country);"),
md("## 5. Runtime skew\n\nРавномерное хранение не гарантирует равномерный запрос. Фильтр, JOIN или GROUP BY может оставить на одном сегменте намного больше строк. Поэтому анализируют и policy таблицы, и фактическое распределение промежуточного результата."),
md("### Filter skew\n\nТаблица по event_id может оставаться равномерной после фильтра страны. Таблица по country отправит все строки одной страны одному content. Это может уменьшить число работающих сегментов до одного."),
md("### Join skew\n\nПри Redistribute частое значение JOIN-ключа собирается у одного получателя. Особенно опасны `unknown`, пустые значения и NULL. Остальные сегменты заканчивают раньше и ждут перегруженный."),
md("### Aggregation skew\n\nЧастичная агрегация уменьшает сеть, но крупнейшая группа всё равно обрабатывается одним получателем финальной стадии. Отличайте локальный и финальный aggregate в плане."),
md("## 6. Distribution и partitioning\n\nDistribution отвечает «на каком сегменте строка», partitioning — «в какой физической части». Таблица может быть партиционирована по дате и распределена по visitid. Ключи решают разные задачи и не обязаны совпадать."),
md("## 7. Порядок работы\n\n1. Назовите гранулярность. 2. Измерьте cardinality, NULL и top frequency. 3. Перечислите крупные JOIN/GROUP BY. 4. Создайте варианты. 5. Посчитайте row/byte skew. 6. Сравните EXPLAIN и Motion. 7. Проверьте runtime skew. 8. Сформулируйте рекомендацию по измерениям."),
]
for n,(obj,prompt,hint) in enumerate(tasks,1):
    if n==11: cells.append(md("## Уровень 2 — JOIN и Motion"))
    if n==21: cells.append(md("## Уровень 3 — runtime skew и проектирование Метрики"))
    task_body = f"### Задание {n}. `m_razhin.{obj}`\n\n**Что сделать:** {prompt}\n\nПеред созданием объекта зафиксируйте ожидаемое распределение или план. После создания сравните ожидание с измерением."
    if n == 1:
        task_body += """

**Вход:** `greenplum_training.dist_source`, grain — одно событие, 100000 строк,
distribution policy — `DISTRIBUTED BY (event_id)`.

**Целевой результат:** VIEW `m_razhin.gpd_01_segment_rows` с двумя колонками:

| Колонка | Смысл |
|---|---|
|`segment_id`|значение системного `gp_segment_id`|
|`rows_count`|число строк источника на этом сегменте|

**Алгоритм без готового решения:**

1. Проверьте колонки источника через `information_schema.columns`.
2. Убедитесь, что `segment_id` среди них отсутствует.
3. Сгруппируйте строки по системному идентификатору физического сегмента.
4. Переименуйте этот идентификатор в `segment_id` в выходном VIEW.
5. Проверьте, что получены четыре строки, а сумма `rows_count` равна 100000.

**Что проверяет checker:** точное имя VIEW, четыре сегментные строки и сохранение всех
100000 исходных строк. Обычный `SELECT` не проходит: результат необходимо сохранить в VIEW.

**Типичные ошибки:** `segment_id` вместо `gp_segment_id`; `CREATE VIEW IF EXISTS`
(такого синтаксиса нет); пропущенное `AS`; выполнение SELECT без создания VIEW.
"""
    task_body += f"\n\n<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"
    cells += [
      md(task_body),
      code(f"%%sql\nSET search_path TO m_razhin,public;\n-- DROP VIEW/TABLE IF EXISTS m_razhin.{obj};\n-- Создайте требуемый объект здесь."),
      code(f"%%sql\n-- Ручная проверка\n-- SELECT * FROM m_razhin.{obj} LIMIT 20;"),
      *([md("<details><summary><strong>Эталонное решение и разбор</strong></summary>\n\n"
            f"```sql\n{SOLUTIONS[n][0]}\n```\n\n**Почему так:** {SOLUTIONS[n][1]}\n\n"
            "После выполнения сравните policy, сумму строк по сегментам и коэффициент skew.\n\n</details>")]
        if n in SOLUTIONS else []),
      code(f"%%sql\nSELECT * FROM greenplum_training.run_checks('distribution',{n});")
    ]
cells += [md("## Прогресс"),code("%%sql\nSELECT * FROM greenplum_training.progress WHERE module_name='distribution' ORDER BY task_no;")]
nb=nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3 (ipykernel)","language":"python","name":"python3"}})
OUTPUT.parent.mkdir(parents=True,exist_ok=True); nbf.write(nb,OUTPUT); print(OUTPUT)
