# 爬虫工程

使用Kafka架构做消息队列，Structured Streaming 对接数据到HDFS以及做ETL工作

![](./imgs/pipeline_after.png)

## 执行程序

各爬虫主题的目录下`main_run.sh`脚本为程序入口，可设置为定时任务，或者手动执行. 

`$ bash main_run.sh`

当前所有自动化脚本工作部署在entrobus32机器上, 具体自动化脚本配置在`/home/liujs/etc/mycrontab`

每4小时执行一次，在crontab的配置文件中加入(注意由于crontab使用自己的一套环境变量，需要把环境变量加入到main_run.sh中)
```
# 每隔4个小时从kafka处理机场查询数据
0 */4 * * * bash /home/liujs/crawler/direction_amap/main_run.sh
11 */4 * * * bash /home/liujs/crawler/direction_baidu/main_run.sh
# 每隔7天备份一次Kafka的百度查询数据
0 1 */7 * * bash /home/liujs/crawler/direction_baidu/backup/backup_source.sh
```

`$ crontab mycrontab`

## Kafka 架构

[Kafka概念](http://kafka.apache.org/intro)

[官方入门文档](http://kafka.apache.org/quickstart)

Kafka版本：kafka_2.12-2.2.0 , kafka目录: `export KAFKA_HOME=/home/liujs/usr/local/kafka`

zookeeper集群: entrobus32:2181,entrobus12:2181,entrobus28:2181/kafka1 (Kafka注册信息在zookeeper的/kafka1下)

Kafka集群: entrobus32:9092,entrobus28:9092,entrobus12:9092 
```
id0: entrobus32:9092
id1: entrobus28:9092
id2: entrobus12:9092
```

Kafka配置文件server.properties
```
...
# kafka在zookeeper的注册信息位置，一般会在zookeeper根目录下创建chroot，我们这里是kafka1
zookeeper.connect=entrobus32:2181,entrobus12:2181,entrobus28:2181/kafka1
# 日志信息存放路径
log.dirs=/home/liujs/kafka-logs

# broker的分区默认设置
num.partitions=2

# default replication for auto created topic
# 自动创建的主题默认副本数
default.replication.factor=2

# 默认消费者offset的副本数量设置，对于生产环境建议大于1
offsets.topic.replication.factor=2
transaction.state.log.replication.factor=2
transaction.state.log.min.isr=2
...
```

启动kafka与停止kafka(在对应broker所在的机器下操作) 
```
# 启动守护进程, 打开JMX用于kafka-manager查看metric
export JMX_PORT=9988
kafka-server-start.sh -daemon $KAFKA_HOME/config/server.properties
# 停止Kafka broker
kafka-server-stop.sh
# 查看当前Kafka进程
jps
```

常用Topic工具

```
查看主题
kafka-topics.sh --list --bootstrap-server entrobus32:9092

查看是否有数据
kafka-console-consumer.sh --bootstrap-server entrobus32:9092 \
--topic directionbaidu --from-beginning

描述主题
kafka-topics.sh --describe --bootstrap-server entrobus32:9092 \
--topic direction_amap

创建主题
kafka-topics.sh --create \
--bootstrap-server entrobus32:9092 \
--replication-factor 2 --partitions 2 \
--topic directionbaiduss

删除主题
kafka-topics.sh --delete --bootstrap-server entrobus32:9092 \
--topic directionamap
```

增加主题的副本数, 需要创建处理的json文件，利用kafka-reassign-partitions.sh工具进行处理.[官方参考资料](http://kafka.apache.org/documentation/#operations)

1. 查看当前主题的分区Partitions和副本数Replications (副本有两个概念，一个是所有副本Replicas，一个是同步副本Isr)
```
kafka-topics.sh --describe --bootstrap-server entrobus32:9092 \
--topic direction_amap
```

2. 创建increase-replication-factor.json文件，内容如下：
```
{
    "version": 1,
    "partitions": [{
            "topic": "bus8684",
            "partition": 0,
            "replicas": [0, 2]
        }]
}
```
3. 执行计划, 注意zookeeper的位置必须为chroot
```
kafka-reassign-partitions.sh --zookeeper entrobus32:2181/kafka1 --reassignment-json-file increase-replication-factor.json --execute
```

kafka 监控工具: [kafka-manager](https://github.com/yahoo/kafka-manager)

监控地址： [http://entrobus32:10005](http://entrobus32:10005)

当前kafka-manager目录为32号机/home/liujs/usr/local/kafka-manager
```
启动kafka-manager
cd $KAFKA_MANAGER_HOME
nohup bin/kafka-manager -Dhttp.port=10005 &
```

可以查看当前的broker/topic信息


使用pyspark调试:

```
# 需要加载依赖jar包 (为了使用kafka和delta)
pyspark --packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.3,io.delta:delta-core_2.11:0.2.0 \
--master yarn \
--num-executors 3 \
--driver-memory 4g \
--executor-memory 2g \
--executor-cores 1
```

## 爬虫主题定义：

* poibaidu: 取消
* qqhouse: 有数据
* fang（租房频道）: 有数据
* fangesf（二手房买卖；开发中；计划下周完成）: 有数据
* gzmtr（爬虫等待重写；字段等待重新整理）: 暂无数据
* dianping（需要等待比较长的时间来自动化）: 暂无数据
* easygo（需要等待比较长的时间来自动化）: 暂无数据
* tianyancha（采用抓包工具爬取；需要等待比较长时间解决从本地windows10上传集群的通讯问题）: 暂无数据
* direction_amap/directionbaidu

    实时爬取碧桂园总部往返广州白云机场和深圳宝安机场的数据。已完成Data Injection和ETL工作

* shop58

    58同城商铺数据