from pathlib import Path
import nbformat as nbf
R=Path(__file__).resolve().parent.parent
O=R/'notebooks';O.mkdir(parents=True,exist_ok=True)
def md(x):return nbf.v4.new_markdown_cell(x)
cells=[
md("""# Каталог учебных данных

Этот справочник используется курсами SQL, Greenplum, Hadoop и Spark. Его задача — до
написания запроса ответить на четыре вопроса: что означает строка, какой ключ её
идентифицирует, как таблицы связаны и какие ошибки качества возможны.

## Как читать описание

- **Grain** — смысл одной строки.
- **Business key** — устойчивый идентификатор сущности из источника.
- **Technical key** — созданный системой surrogate/hash/identity key.
- **Cardinality** — сколько строк одной стороны соответствует строке другой.
- **Nullable** не означает «значение необязательно для бизнеса»: NULL может быть
  следствием отсутствующей стадии процесса, ошибки или несовпавшего JOIN.
"""),
md("""# 1. Olist — электронная коммерция

Olist используется в SQL-курсе. Raw-таблицы содержат текстовые поля источника,
`staging` приводит типы, `mart` задаёт готовые аналитические grains.

```text
customers 1 ── N orders 1 ── N order_items N ── 1 products
                       │              │
                       │              └──────── N:1 sellers
                       ├── 1:N order_payments
                       └── 1:N order_reviews
products N ── 1 product_category_translation
customers/sellers N ── 1 aggregated geolocation by zip_code_prefix
```

Критическая ловушка: одновременно присоединить `order_items` и `order_payments` к
`orders` без предварительной агрегации. Заказ с 3 позициями и 2 платежами даст 6 строк,
а суммы умножатся. Правильное рассуждение начинается с целевого grain.
"""),
md("""## 1.1 Таблицы Olist

| Объект | Grain | Ключ | Важные поля | Риски |
|---|---|---|---|---|
|`staging.customers`|одна регистрация покупателя|`customer_id`|`customer_unique_id`, city, state|один человек может иметь несколько customer_id|
|`staging.orders`|один заказ|`order_id`|status и пять timestamps|не все стадии доставки заполнены|
|`staging.order_items`|позиция заказа|`order_id, order_item_id`|product, seller, price, freight|несколько строк на заказ|
|`staging.order_payments`|часть оплаты|`order_id, payment_sequence`|type, installments, value|несколько способов оплаты|
|`staging.order_reviews`|отзыв/версия отзыва|не полагаться только на `order_id`|score, message, timestamps|возможны несколько отзывов|
|`staging.products`|товар|`product_id`|category, dimensions, weight|неизвестная категория и NULL характеристик|
|`staging.sellers`|продавец|`seller_id`|zip, city, state|география по почтовому индексу|
|`staging.geolocation`|агрегированный zip|`zip_code_prefix`|lat, lon, city, state|сырой источник N строк на zip|

`mart.order_finance` имеет grain заказа. Позиции и платежи заранее агрегированы отдельно.
`mart.product_sales` имеет grain товара. `mart.customer_summary` — уникального покупателя.
"""),
md("""## 1.2 Как проверять Olist

1. Сравнить `count(*)` и `count(distinct candidate_key)`.
2. Посчитать NULL по обязательным и процессным полям отдельно.
3. Перед JOIN записать ожидаемую кратность 1:1, 1:N или N:M.
4. После JOIN сверить число ключей и сумму метрики с источником.
5. Для денег не усреднять уже усреднённые группы без весов.

Контрольная формула финансового заказа не требует равенства `product + freight = payment`
для каждой строки без исследования отмен, vouchers и округления; расхождение сначала
измеряют и классифицируют.
"""),
md("""# 2. eBay — снимки объявлений

Физический путь: `/data/raw/ebay/snapshot_dt=YYYY-MM-DD/*.snappy.parquet`.
Формат Parquet, compression Snappy. В проверенном наборе 2 501 511 строк, 24 колонки,
25 файлов. Основной аналитический grain — наблюдение объявления `itemid` в дату
`snapshot_dt`; перед использованием ключ необходимо проверить на дубли.

```text
snapshot_dt
   └── itemid
       ├── товар: title, price, condition, buying_options
       ├── иерархия: category → sub_category → sub_sub_category
       ├── продавец: seller_name, feedback_percentage, feedback_score
       ├── география: location_country
       └── доставка: shipping_cost/type/currency, delivery_days
```
"""),
md("""## 2.1 Колонки eBay

| Группа | Колонки | Тип/смысл | Проверки |
|---|---|---|---|
|Идентификация|`snapshot_dt`, `itemid`|date + string|NULL и уникальность пары|
|Карточка|`title`, `item_condition`, `top_rated_buying_experience`|описание и признаки|пустые строки, domain|
|Цена|`price`, `currency`|double + ISO-like code|неотрицательность, валюта|
|Категории|`category_*`, `sub_category_*`, `sub_sub_category_*`|денормализованная иерархия|конфликты id/name|
|Продавец|`seller_name`, feedback fields|имя, процент, счётчик|процент 0..100, NULL|
|Доставка|`shipping_cost*`, `estimated_delivery_days`|стоимость и срок|валюта, отрицательные значения|
|Время|`item_creation_ts`|timestamp|не позже snapshot без объяснения|

`snapshot_dt` одновременно присутствует в schema файлов и выводится из имени partition,
поэтому Spark может предупреждать о повторе. Это сигнал проверить контракт записи, а не
просто подавить warning.
"""),
md("""# 3. Yandex Metrica — визиты

Hive: `yndx_metrica_data.metrica`; Greenplum/PXF:
`dds.ext_raw_yndx_metrica_logs`; HDFS: `/data/raw/yndx_metrica/parquet/date=YYYY`.

Grain — один визит. `visitid` уникален только в оговорённой области (например, год),
поэтому глобальный ключ проверяется составом полей. `_date` — дата визита, `date` — годовая
partition column. Их нельзя считать взаимозаменяемыми.

| Группа | Поля |
|---|---|
|Ключ/время|`visitid`, `_date`, `dt`, partition `date`|
|Пользователь|`clientid`, `isnewuser`, `ipaddress`|
|География|`regioncountry`, `regioncity`, `clienttimezone`|
|Устройство|`devicecategory`, `mobilephone`, `mobilephonemodel`|
|ПО|`operatingsystem`, `browser`|
|Маршрут|`starturl`, `endurl`|
|Метрики|`pageviews`, `visitduration`|

Для Greenplum поля date/country/city/ip участвуют в регулярных фильтрах, но ключ
распределения выбирают по равномерности и JOIN, а не потому что колонка есть в WHERE.
"""),
md("""# 4. MOEX — сделки

HDFS: `/moex_labs/raw/trades/secid=<ticker>/trade_session_date=<date>/`.
Целевой grain — отдельная сделка/наблюдение торгового потока. Витрина выбирает крупнейшую
сделку на тикер, день и тип BUY/SELL; при равной VALUE нужен детерминированный tie-breaker.

| Поле | Смысл |
|---|---|
|`BOARDID`, `BOARD_NAME`|режим торгов и его название|
|`ISIN`, `SECID`|международный и биржевой код бумаги|
|`ISQUALIFIEDINVESTORS`|ограничение для квалифицированных инвесторов|
|`PRICE`, `VALUE`, `QUANTITY`|цена, сумма и количество|
|`DEAL_TYPE`|BUY или SELL|
|`DEAL_TIME`|время сделки внутри сессии|
|`TRADE_SESSION_DATE`|торговая дата|

Нельзя восстанавливать BUY/SELL случайным образом при наличии исходного признака. Нельзя
выбирать `max(value)` и произвольные остальные колонки: используйте ранжирование целых строк.
"""),
md("""# 5. Выбор набора по теме

| Курс/тема | Основной набор | Почему |
|---|---|---|
|SQL, транзакции, функции, JOIN|Olist|реляционные связи и разные grains|
|Greenplum distribution/PXF|Yandex Metrica|объём, фильтры, HDFS external|
|Greenplum marts|MOEX|факт сделки и top-per-group|
|Hadoop/Hive|eBay|физические partitions и Parquet|
|Spark|eBay|2.5 млн строк, аналитика snapshots|

## Универсальная карточка перед решением

1. Что означает входная строка?
2. Что должна означать выходная строка?
3. Какой ключ обязан быть уникален?
4. Где допустим NULL?
5. Может ли JOIN размножить строку?
6. Какая метрика должна сохраниться?
7. Как доказать результат независимой проверкой?
""")]
nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3 (ipykernel)','language':'python','name':'python3'}})
nbf.write(nb,O/'00_Data_Catalog_and_Schemas.ipynb')
