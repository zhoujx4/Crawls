# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import socket
import json
import time

class WeatherPipeline(object):

    cluster_servers_for_spiders = ["entrobus32", "entrobus28", "entrobus12"]
    cluster_servers_for_kafka = ["entrobus32:9092","entrobus28:9092","entrobus12:9092"]


    def init_self_attributes(self, spider):
        self.to_kafka = True
        self.kafka_topic = spider.name
        self.kafka_producer = None



        if socket.gethostname() in self.cluster_servers_for_spiders:
            if self.kafka_producer is None:
                from kafka import KafkaProducer
                self.kafka_producer = KafkaProducer( bootstrap_servers=self.cluster_servers_for_kafka)

    # def pipeline_to_kafka(self, spider, key_list, item_list, kafka_topic_str, kafka_producer_obj):
    #     kafka_producer_obj.send(kafka_topic_str, bytes(json.dumps(dict(zip(key_list, item_list))), encoding="utf-8"), timestamp_ms=int(time.time() * 1000))

    def process_item(self, item, spider):
        self.init_self_attributes( spider = spider)
        msg = dict(item)

        msg = json.dumps(msg)
        msg = bytes(msg, encoding="utf=8")
        if self.to_kafka == True:
            self.kafka_producer.send(self.kafka_topic, msg)

        return item







