# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exporters import JsonLinesItemExporter,CsvItemExporter
from datetime import datetime
import numpy as np
import requests
import json
import socket
import kafka
from kafka import KafkaProducer

base_gaode_url = "https://restapi.amap.com/v3/geocode/geo?parameters"
headers = {
    'Accept': 'application/json,text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en,zh-cn.utf-8',
    # "Referer": "https://restapi.amap.com/v3/place/text",
}
cluster_servers_for_spiders = ["entrobus32", "entrobus28", "entrobus12"]
cluster_servers_for_kafka = ["entrobus32:9092","entrobus28:9092","entrobus12:9092"]



class TudinetPipeline(object):
    def __init__(self):
        self.json = open('./output/tudinet_zpg_{}.json'.format(datetime.now().strftime('%Y-%m-%d')), 'ab')
        self.json_exporter = JsonLinesItemExporter(self.json, ensure_ascii=False, encoding='utf-8')
        self.csv = open('./output/tudinet_zpg_{}.csv'.format(datetime.now().strftime('%Y-%m-%d')), 'ab')
        self.csv_exporter = CsvItemExporter(self.csv, encoding='utf-8')
        self.kafka_producer = None

    def to_kafka(self, spider):
        if socket.gethostname() in cluster_servers_for_spiders:
            self.to_kafka = True
        else:
            self.to_kafka = False
        self.kafka_topic = spider.name

        if socket.gethostname() in cluster_servers_for_spiders and self.to_kafka:
            if self.kafka_producer is None:
                self.kafka_producer = KafkaProducer( bootstrap_servers = cluster_servers_for_kafka )


    def open_spider(self, spider):
        #导入kafka信息
        self.to_kafka(spider)
        print("爬虫开始了")

    def process_item(self, item, spider):
        self.json_exporter.export_item(item)
        self.csv_exporter.export_item(item)
        #保存到kafka
        msg = dict(item)
        msg = json.dumps(msg)
        msg = bytes(msg, encoding='utf=8')
        if self.to_kafka == True:
            self.kafka_producer.send(self.kafka_topic, msg)
        return item

    def close_spider(self, spider):
        self.json.close()
        self.csv.close()
        print("爬虫结束了")










