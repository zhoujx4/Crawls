from pyspark.sql import SparkSession
from pyspark.sql.types import StringType, ArrayType, StructType
from pyspark.sql.functions import from_json, explode, col


spark = SparkSession.builder.appName("direction_amap_source_injection").getOrCreate()
source_path = "crawler/direction_amap/source_delta_2019-07-20"

# 读取主题数据
brokers = "entrobus32:9092,entrobus28:9092,entrobus12:9092"
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", brokers) \
    .option("subscribe", "direction_amap") \
    .option("startingOffsets", "earliest") \
    .load()

# 抽取value以及timestamp
df = df.selectExpr("CAST(value AS STRING)", "timestamp")

# 写入到crawler/qqhouse里
query = df.writeStream.format("delta"). \
    trigger(once=True). \
    option("path", source_path). \
    option("checkpointLocation", source_path + "/checkpoints"). \
    start()

query.awaitTermination()

