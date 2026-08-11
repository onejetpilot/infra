from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[2]
MAPS=[ROOT/'sql/notebooks/00_SQL_Course_Map.ipynb',ROOT/'greenplum/notebooks/00_Greenplum_Course_Map.ipynb',ROOT/'hadoop/notebooks/00_Hadoop_Course_Map.ipynb',ROOT/'spark/notebooks/00_Spark_Course_Map.ipynb']
def md(x):return nbf.v4.new_markdown_cell(x)
for p in MAPS:
 nb=nbf.read(p,4);nb.cells=[c for c in nb.cells if c.metadata.get('course_map_enhancer')!='v1']
 extra=[md('''## Как устроено обучение

Ноутбук — не сборник рецептов. Каждый модуль проходит четыре уровня: ментальная модель и
архитектура; демонстрации механизма; задания от базового к инженерному; автоматическая
проверка и собственное объяснение. До кода сформулируйте grain, key, NULL и ожидаемое
физическое выполнение. PASS означает выполненный контракт, но не заменяет понимание.'''),md('''## Общий каталог данных

Откройте `data-catalog/00_Data_Catalog_and_Schemas.ipynb`. Там описаны связи и grains
Olist, физические partitions и 24 колонки eBay, visit grain Yandex Metrica и trade grain
MOEX, а также ключи, NULL, качество и опасные JOIN. Если вы не можете одним предложением
описать входную строку, к запросу переходить рано.'''),md('''## Универсальный цикл задания

```text
контракт → grain/key/NULL/объём → прогноз logical/physical result
        → минимальная реализация → независимые проверки
        → checker → объяснить каждый PASS/FAIL
```

Готовые решения отсутствуют. Подсказка ограничивает поиск, но не выбирает за вас ключ,
frame, distribution, partition или цепочку transformations.''')]
 for c in extra:c.metadata['course_map_enhancer']='v1'
 nb.cells[1:1]=extra
 for c in nb.cells:
  if c.cell_type=='code':c.outputs=[];c.execution_count=None
 nbf.write(nb,p)
