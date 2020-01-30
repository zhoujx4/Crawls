from pyspark.sql import SparkSession
from pyspark.sql.types import StringType, ArrayType, StructType
from pyspark.sql.functions import from_json, explode, col, element_at


# 解析path的UDF
def parse_path(traffic, path):
    paths = path.split(";")
    rlt = []
    start = 0
    for (status, geo_cnt, distance) in traffic:
        rlt.append([status, ";".join(paths[start:start+int(geo_cnt)+1])])
        start = start + int(geo_cnt)
    return rlt


spark = SparkSession.builder.appName("direction_baidu_etl").getOrCreate()
parse_path_udf = spark.udf.register("parse_path", lambda traffic, path: parse_path(traffic, path), \
                                    ArrayType(ArrayType(StringType())))

# 定义解析的JSON数据
traffic_condition_schema = StructType(). \
    add("status", StringType()). \
    add("geo_cnt", StringType()). \
    add("distance", StringType())
location_schema = StructType(). \
    add("lng", StringType()). \
    add("lat", StringType())
selected_path_schema = StructType(). \
    add("leg_index", StringType()). \
    add("road_name", StringType()). \
    add("direction", StringType()). \
    add("distance", StringType()). \
    add("road_type", StringType()). \
    add("toll", StringType()). \
    add("toll_distance", StringType()). \
    add("traffic_condition", ArrayType(traffic_condition_schema)). \
    add("path", StringType()). \
    add("start_location", location_schema). \
    add("end_location", location_schema)
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
    .option("subscribe", "directionbaidu") \
    .option("startingOffsets", "earliest") \
    .load()

# 抽取value以及timestamp
df = df.selectExpr("CAST(value AS STRING)", "timestamp")

# value解析成JSON
# 解析JSON字段为列
etl_df = df.select(from_json("value", direction_schema).alias("parsed_value"), "timestamp")
for name in direction_schema.fieldNames():
    etl_df = etl_df.withColumn(name, col("parsed_value").getField(name))
    
etl_df = etl_df.drop("parsed_value", "strategy", "count", "now", "url", "project", "spider", "server", "date", "path")
etl_df = etl_df.withColumnRenamed("duration", "total_duration")

etl_df = etl_df.withColumn("selected_path_steps", explode("selected_path_steps"))
for name in selected_path_schema.fieldNames():
    etl_df = etl_df.withColumn(name, col("selected_path_steps").getField(name))
etl_df = etl_df.drop("selected_path_steps", "direction", "toll", "toll_distance", \
                     "road_type", "leg_index", "road_name", "paths", "distance", "start_location", "end_location")

etl_df = etl_df.withColumn("status_path", parse_path_udf("traffic_condition", "path"))
etl_df = etl_df.drop("traffic_condition", "path")
etl_df = etl_df.withColumn("status_path", explode("status_path"))

etl_df = etl_df.withColumn("status", element_at("status_path", 1))
etl_df = etl_df.withColumn("polyline", element_at("status_path", 2))
etl_df = etl_df.drop("status_path")
etl_df = etl_df.select("timestamp", "preset_route", "total_duration", "status", "polyline")

query = etl_df.writeStream.format("delta"). \
    trigger(once=True). \
    option("path", "crawler/directionbaidu/clean_delta_2019-07-19"). \
    option("checkpointLocation", "crawler/directionbaidu/clean_delta_2019-07-19/checkpoints"). \
    start()
query.awaitTermination()

# clean_csv = spark.read.parquet("crawler/directionbaidu/clean_parquet_newkafka")
# clean_csv.repartition(1).write.mode("overwrite").csv("crawler/directionbaidu/clean_csv_newkafka", header=True)

source_path = "crawler/directionbaidu/clean_delta_2019-07-19"

clean_json = spark.read.format("delta").load(source_path)
clean_json = clean_json.select("timestamp", "preset_route", "total_duration")
clean_json = clean_json.dropDuplicates()
clean_json.repartition(1).write.mode("overwrite").json("crawler/directionbaidu/clean_json")

# toPandas take a lot of time
# # save to csv
# clean_csv.toPandas().to_csv("/home/liujs/crawler/direction_baidu/clean_csv.csv", header=True, index=False)
# # save to json lines witch is compatible with spark
# clean_csv.toPandas().to_json("/home/liujs/crawler/direction_baidu/directionbaidu_data.json", orient="records", lines=True)
