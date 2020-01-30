from pyspark.sql import SparkSession
from pyspark.sql.types import StringType, ArrayType, StructType
from pyspark.sql.functions import from_json, explode, col


spark = SparkSession.builder.appName("direction_amap_etl").getOrCreate()

# direction 数据结构
tmcs_schema = StructType(). \
    add("distance", StringType()). \
    add("lcode", StringType()). \
    add("polyline", StringType()). \
    add("status", StringType())

selected_path_schema = StructType(). \
    add("instruction", StringType()). \
    add("orientation", StringType()). \
    add("distance", StringType()). \
    add("tolls", StringType()). \
    add("toll_distance", StringType()). \
    add("toll_road", (StringType())). \
    add("duration", StringType()). \
    add("polyline", StringType()). \
    add("action", StringType()). \
    add("assistant_action", (StringType())). \
    add("tmcs", ArrayType(tmcs_schema)). \
    add("cities", StringType())

direction_schema = StructType(). \
    add("preset_route", StringType()). \
    add("strategy", StringType()). \
    add("duration", StringType()). \
    add("count", StringType()). \
    add("paths", StringType()). \
    add("now", StringType()). \
    add("selected_path_steps", ArrayType(selected_path_schema)). \
    add("url", StringType()). \
    add("project", StringType()). \
    add("spider", StringType()). \
    add("server", StringType()). \
    add("date", StringType())

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

# value解析成JSON
# 解析JSON字段为列
etl_df = df.select(from_json("value", direction_schema).alias("parsed_value"), "timestamp")

for name in direction_schema.fieldNames():
    etl_df = etl_df.withColumn(name, col("parsed_value").getField(name))

etl_df = etl_df.drop("parsed_value", "url", "project", "spider", "server", "strategy")
etl_df = etl_df.withColumnRenamed("duration", "total_duration")

etl_df = etl_df.withColumn("selected_path_steps", explode("selected_path_steps"))

for name in selected_path_schema.fieldNames():
    etl_df = etl_df.withColumn(name, col("selected_path_steps").getField(name))
    
etl_df = etl_df.drop("selected_path_steps")
etl_df = etl_df.select("timestamp", "preset_route", "total_duration", "tmcs")
etl_df = etl_df.withColumn("tmcs", explode("tmcs"))

for name in tmcs_schema.fieldNames():
    etl_df = etl_df.withColumn(name, col("tmcs").getField(name))

etl_df = etl_df.drop("tmcs", "distance", "lcode")
etl_df = etl_df.select("timestamp", "preset_route", "total_duration", "status", "polyline")

etl_path = "crawler/direction_amap/clean_delta_2019-07-20"
checkpoints_path = etl_path + "/checkpoints"
query = etl_df.writeStream.format("delta"). \
    trigger(once=True). \
    option("path", etl_path). \
    option("checkpointLocation", checkpoints_path). \
    start()

query.awaitTermination()

# clean_csv = spark.read.format("delta").load(etl_path)
# clean_csv.repartition(1).write.mode("overwrite").csv("crawler/direction_amap/clean_csv_newkafka", header=True)
