#!/bin/bash
export ANACONDA_HOME=/home/hadoop/anaconda3
export JAVA_HOME=/usr/local/jdk1.8.0_131
export SCALA_HOME=/usr/local/scala-2.11.8
export PATH=$ANACONDA_HOME/bin:$JAVA_HOME/bin:$PATH:$SCALA_HOME/bin

export SPARK_HOME=~/usr/local/spark
export PATH=$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH
export PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib


spark-submit \
--packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.3,io.delta:delta-core_2.11:0.2.0 \
--master yarn \
--deploy-mode cluster \
--driver-memory 4g \
--conf "spark.pyspark.driver.python=/home/hadoop/anaconda3/bin/python" \
--conf "spark.pyspark.python=/home/hadoop/anaconda3/bin/python" \
/home/liujs/crawler/direction_baidu/source.py

spark-submit \
--packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.3,io.delta:delta-core_2.11:0.2.0 \
--master yarn \
--deploy-mode cluster \
--driver-memory 4g \
--conf "spark.pyspark.driver.python=/home/hadoop/anaconda3/bin/python" \
--conf "spark.pyspark.python=/home/hadoop/anaconda3/bin/python" \
/home/liujs/crawler/direction_baidu/ETL.py

