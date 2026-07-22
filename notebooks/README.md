# Jupyter notebooks

JupyterLab сохраняет `.ipynb` в этом каталоге, поэтому они остаются после перезапуска
или пересоздания контейнера. По умолчанию пользовательские ноутбуки не добавляются в Git.

Для подключения к Spark, Hive Metastore и HDFS используйте первую ячейку:

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("ebay-notebook")
    .enableHiveSupport()
    .getOrCreate()
)

spark.sql("SHOW DATABASES").show(truncate=False)
```

Zeppelin по-прежнему хранит свои notes отдельно, в Docker volume `zeppelin-notebooks`.
