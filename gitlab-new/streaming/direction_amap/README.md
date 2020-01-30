# Direction Data ETL

设置定时任务进行Kafka数据导入HDFS，Kafka数据ETL到HDFS，转化Parquet成csv格式:

```bash

```


Data injection and ETL submit code
```bash
spark-submit \
--packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.3 \
--master yarn \
--deploy-mode cluster \
--conf "spark.pyspark.driver.python=/home/hadoop/anaconda3/bin/python" \
--conf "spark.pyspark.python=/home/hadoop/anaconda3/bin/python" \
./ETL.py

spark-submit \
--packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.3 \
--master yarn \
--deploy-mode cluster \
--conf "spark.pyspark.driver.python=/home/hadoop/anaconda3/bin/python" \
--conf "spark.pyspark.python=/home/hadoop/anaconda3/bin/python" \
./source.py
```