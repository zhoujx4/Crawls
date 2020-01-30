from pyspark.sql import SparkSession
from pyspark.sql.types import StringType, ArrayType, StructType
from pyspark.sql.functions import from_json, explode, col


spark = SparkSession.builder.appName("directionbaidu_source_injection").getOrCreate()

# 读取主题数据
brokers = "entrobus32:9092,entrobus28:9092,entrobus12:9092"
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", brokers) \
    .option("subscribe", "directionbaidu") \
    .option("startingOffsets", "earliest") \
    .load()

# 抽取value以及timestamp
df = df.selectExpr("CAST(value AS STRING)", "timestamp")

# 写入到crawler/qqhouse里
query = df.writeStream.format("delta"). \
    trigger(once=True). \
    option("path", "crawler/directionbaidu/source_delta_2019-07-19"). \
    option("checkpointLocation", "crawler/directionbaidu/source_delta_2019-07-19/checkpoints"). \
    start()

query.awaitTermination()

