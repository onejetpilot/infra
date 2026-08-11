import os
from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parent.parent
OUTPUT=Path(os.environ.get("GREENPLUM_MARTS_OUTPUT",ROOT/"notebooks"/"07_Data_Marts_30_Tasks.ipynb"))
tasks=[
("gpm_01_grain","Создайте VIEW-контракт гранулярности витрины крупных сделок.","Одна строка должна быть однозначно описана."),
("gpm_02_dim_board","Создайте измерение режима торгов.","Малое измерение можно replicated."),
("gpm_03_dim_security","Создайте измерение инструмента с surrogate key.","SECID остаётся business key."),
("gpm_04_dim_date","Создайте календарь диапазона source.","Добавьте месяц, квартал, weekday."),
("gpm_05_fact_trade","Создайте детальный факт сделок.","Distribution и partitioning выбираются по запросам."),
("gpm_06_fact_quality","Проверьте ключи, NULL, положительные суммы и тип сделки.","Quality до публикации."),
("gpm_07_fact_join","Свяжите факт с измерениями без потерь.","Контролируйте many-to-many."),
("gpm_08_daily_base","Создайте дневной агрегат по SECID/deal_type.","Определите measures и grain."),
("gpm_09_top_trade","Найдите крупнейшую сделку каждого SECID/type/day.","row_number с tie-breaker."),
("gpm_10_top_ties","Сохраните число ничьих максимальной VALUE.","Бизнес должен решить ties."),
("gpm_11_required_mart","Создайте витрину полей исходного Greenplum-задания.","BOARDID…TRADE_SESSION_DATE."),
("gpm_12_mart_policy","Создайте VIEW обоснования storage/distribution/partition.","Рекомендация измерима."),
("gpm_13_liquidity_daily","Создайте дневную ликвидность: trades, quantity, value.","Одна строка SECID/day."),
("gpm_14_liquidity_rank","Добавьте ранг инструмента по обороту внутри дня.","dense_rank."),
("gpm_15_price_daily","Создайте open/high/low/close по времени сделок.","Open/close требуют порядка."),
("gpm_16_prev_close","Добавьте close предыдущего активного дня.","lag после дневной агрегации."),
("gpm_17_price_change","Рассчитайте absolute и percent change.","NULLIF prev_close."),
("gpm_18_monthly","Создайте месячную витрину ликвидности/цен.","Не усредняйте проценты без смысла."),
("gpm_19_seasonality","Создайте сезонность по SECID/month_num.","Сравнивайте активные дни."),
("gpm_20_data_quality","Создайте дневную quality mart.","Snapshot,active,distinct,zero/rejected."),
("gpm_21_scd_security","Создайте SCD2 инструмента.","Одна current version."),
("gpm_22_asof_join","Свяжите сделки с исторической версией security.","Event time внутри valid interval."),
("gpm_23_late_trade","Покажите перерасчёт дня при late trade.","Delete+insert slice."),
("gpm_24_increment_daily","Реализуйте инкремент дневной витрины.","Публикуйте только проверенный день."),
("gpm_25_increment_monthly","Определите затронутый месяц и пересчитайте его.","Late day меняет month."),
("gpm_26_reconciliation","Сверьте факт и витрины по count/value.","Measures должны сохраняться согласно grain."),
("gpm_27_query_plan","Проверьте pruning/Motion типового запроса витрины.","Фильтр ticker/day/type."),
("gpm_28_serving_view","Создайте стабильный serving VIEW над физической mart.","Consumer contract отделён от storage."),
("gpm_29_publish_audit","Создайте audit публикации версий витрины.","READY→PUBLISHED/FAILED."),
("gpm_30_showcase","Соберите итоговый каталог витрин с grain,SLA,policy,status.","Документируйте все созданные marts."),
]
def md(x): return nbf.v4.new_markdown_cell(x)
def code(x): return nbf.v4.new_code_cell(x)
cells=[
md("# Витрины Greenplum — 30 заданий\n\nМодуль строит внутренние аналитические таблицы и итоговую витрину крупнейших BUY/SELL-сделок. Источник контролируемый, а затем подход переносится на MOEX."),
code("%load_ext sql\n%config SqlMagic.displaylimit = 150\n%sql postgresql+psycopg2://gpadmin@cbdb-coordinator:5432/moex"),
md("## 1. Начинайте с grain\n\nГранулярность отвечает, чему соответствует одна строка. Она определяет ключ, допустимые measures и JOIN. «Дневная витрина» недостаточно: нужно сказать `одна строка на trade_date, secid, deal_type`."),
md("## 2. Факт и измерение\n\nФакт содержит события/измеримые показатели и внешние ключи. Измерение описывает контекст. Денормализация может ускорить serving, но источник атрибутов и история должны быть определены."),
md("## 3. Звезда\n\nStar schema соединяет крупный факт с компактными измерениями. В Greenplum физическая модель важна: факт распределяют по частому крупному JOIN/фильтру, маленькие dimensions могут быть replicated."),
md("## 4. Business и surrogate key\n\nSECID — business key, который приходит из источника. Surrogate key идентифицирует конкретную dimension row/version. Он нужен SCD2 и изоляции warehouse от изменения source identifiers."),
md("## 5. Additive measures\n\nVALUE и QUANTITY обычно суммируются по измерениям. PRICE не является additive: дневная цена требует open/high/low/close или weighted average. Нельзя складывать средние и проценты как обычные суммы."),
md("## 6. Semi-additive\n\nBalance/остаток можно суммировать по инструментам, но не по времени. Для временной оси выбирают last snapshot. Всегда описывайте агрегируемость каждой measure."),
md("## 7. Top-N\n\nКрупнейшая сделка выбирается оконным rank внутри `(date,secid,deal_type)`. `row_number` даёт одну строку, но нужен tie-breaker. `rank` сохраняет все ties и меняет grain/число строк."),
md("## 8. Open и close\n\nMIN/MAX(price) не дают open/close. Нужна первая/последняя сделка по deal_time с детерминированным order. High/low — max/min цены. Weighted price рассчитывается по agreed weight."),
md("## 9. SCD2\n\nИзменение атрибута закрывает текущую version и открывает новую. Fact lookup выполняется по business key и event time. JOIN только current dimension переписывает историю."),
md("## 10. Distribution витрины\n\nServing запросы по одному SECID и диапазону дат могут выиграть от distribution by secid. Но GROUP BY day across all securities потребует Motion. Policy выбирают по самым дорогим регулярным потребителям."),
md("## 11. Partitioning витрины\n\nДневной/месячный факт часто partitioned по trade date/month ради pruning и инкрементной замены. Не создавайте partition на каждый SECID. Distribution и partitioning решают разные оси."),
md("## 12. AO column\n\nШирокие serving marts с выбором части measures подходят AO column + compression. Малые dimensions и audit/control — heap или AO row по характеру изменений."),
md("## 13. Материализация\n\nView хранит запрос, table хранит результат. Сложный расчёт на каждом consumer query может быть дорог. Материализованная mart требует pipeline, freshness, reconciliation и повторяемого refresh."),
md("## 14. Дневные и месячные зависимости\n\nМесячная mart зависит от дневной или детального факта. Late trade меняет день, затем месяц и возможно сезонность. Pipeline должен вычислять downstream affected slices."),
md("## 15. Quality mart\n\nQuality — самостоятельный продукт: snapshot count, active count, distinct instruments, zero/rejected, freshness. Он помогает потребителю понять покрытие и ETL — остановить публикацию."),
md("## 16. Serving contract\n\nСтабильный VIEW может скрывать физическую таблицу/version. Consumer получает фиксированные имена/типы, а команда может пересобрать storage и атомарно переключить underlying object."),
md("## 17. Publish\n\nСтатусы BUILDING→READY→PUBLISHED или FAILED отделяют расчёт от доступности. Публикация происходит только после quality/reconciliation. Audit хранит version, period, counts и timestamps."),
md("## 18. Оптимизация\n\nПроверяйте типовой запрос: ticker/day/type, pruning, Motion, выбранные колонки и runtime skew. Хорошая витрина оптимизирует потребление, а не только процесс загрузки."),
md("## 19. Reconciliation\n\nДля агрегата сумма VALUE/QUANTITY должна согласовываться с фактом в той же области. Top-1 намеренно не сохраняет общую сумму — для него проверяют число групп, принадлежность строк и max rule."),
md("## 20. Порядок\n\nContract grain→dimensions→fact→quality→daily→monthly→serving→plan→incremental refresh→reconciliation→publish audit."),
]
for n,(obj,prompt,hint) in enumerate(tasks,1):
    if n==11: cells.append(md("## Уровень 2 — MOEX marts"))
    if n==21: cells.append(md("## Уровень 3 — history, incremental refresh и serving"))
    cells += [md(f"### Задание {n}. `m_razhin.{obj}`\n\n**Что сделать:** {prompt}\n\nПеред SQL запишите grain, key, measures и physical policy. После — проверьте uniqueness, reconciliation и типовой план.\n\n<details><summary>Подсказка</summary>\n\n{hint}\n\n</details>"),
      code(f"%%sql\nSET search_path TO m_razhin,public;\n-- Создайте m_razhin.{obj}."),
      code("%%sql\n-- Ручная проверка grain/quality/reconciliation."),
      code(f"%%sql\nSELECT * FROM greenplum_training.run_checks('data_marts',{n});")]
cells += [md("## Прогресс"),code("%%sql\nSELECT * FROM greenplum_training.progress WHERE module_name='data_marts' ORDER BY task_no;")]
nb=nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3 (ipykernel)","language":"python","name":"python3"}})
OUTPUT.parent.mkdir(parents=True,exist_ok=True); nbf.write(nb,OUTPUT); print(OUTPUT)
