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
import math

base_gaode_url = "https://restapi.amap.com/v3/geocode/geo?parameters"
headers = {
    'Accept': 'application/json,text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en,zh-cn.utf-8',
    # "Referer": "https://restapi.amap.com/v3/place/text",
}
cluster_servers_for_spiders = ["entrobus32", "entrobus28", "entrobus12"]
cluster_servers_for_kafka = ["entrobus32:9092","entrobus28:9092","entrobus12:9092"]



class Fang_zfPipeline(object):
    def __init__(self):
        self.json = open('./output/fang_zf{}.json'.format(datetime.now().strftime('%Y-%m-%d')), 'ab')
        self.json_exporter = JsonLinesItemExporter(self.json, ensure_ascii=False, encoding='utf-8')
        self.csv = open('./output/fang_zf{}.csv'.format(datetime.now().strftime('%Y-%m-%d')), 'ab')
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
        item = Get_Gaode_POI(item)
        lng = item['longitude']
        lat = item['latitude']
        Baidu_location = gcj02_to_bd09(lng, lat)
        item['longitude'] = Baidu_location[0]
        item['latitude'] = Baidu_location[1]

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

class Fang_xfPipeline(object):
    def __init__(self):
        self.json = open('./output/fang_xf{}.json'.format(datetime.now().strftime('%Y-%m-%d')), 'ab')
        self.json_exporter = JsonLinesItemExporter(self.json, ensure_ascii=False, encoding='utf-8')
        self.csv = open('./output/fang_xf{}.csv'.format(datetime.now().strftime('%Y-%m-%d')), 'ab')
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
        item = Get_Gaode_POI(item)
        lng = item['longitude']
        lat = item['latitude']
        Baidu_location = gcj02_to_bd09(lng, lat)
        item['longitude'] = Baidu_location[0]
        item['latitude'] = Baidu_location[1]

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

class Fang_esfPipeline(object):
    def __init__(self):
        self.json = open('./output/fang_esf_{}.json'.format(datetime.now().strftime('%Y-%m-%d')), 'ab')
        self.json_exporter = JsonLinesItemExporter(self.json, ensure_ascii=False, encoding='utf-8')
        self.csv = open('./output/fang_esf_{}.csv'.format(datetime.now().strftime('%Y-%m-%d')), 'ab')
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
                self.kafka_producer = KafkaProducer(bootstrap_servers=cluster_servers_for_kafka)

    def open_spider(self, spider):
        #导入kafka信息
        self.to_kafka(spider)
        print("爬虫开始了")

    def process_item(self, item, spider):
        item = Get_Gaode_POI(item)
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


x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 扁率


def gcj02_to_bd09(lng, lat):
    """
    火星坐标系(GCJ-02)转百度坐标系(BD-09)
    谷歌、高德——>百度
    :param lng:火星坐标经度
    :param lat:火星坐标纬度
    :return:
    """
    lng = float(lng)
    lat = float(lat)
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * x_pi)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * x_pi)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return [bd_lng, bd_lat]

#请求高德POI点
def Get_Gaode_POI(item):
    item['longitude'] = np.nan
    item['latitude']  = np.nan
    # item['adcode'] = np.nan
    # item['区'] = np.nan

    two_requests_tryout = ['地址']
    for one_tryout in two_requests_tryout:
        result_dict = {}
        # 请求参数
        params = {
            "key" : '4ebb849f151dddb3e9aab7abe6e344e2',
            "address" : str(item[one_tryout]),
            "city" : str(item['城市'])
        }
        response = requests.get(base_gaode_url, headers=headers,params=params)
        if 200 == response.status_code:
            result_dict = parse_gaode_json(response.text)
        if 0 < (result_dict['count']):
            item["longitude"] = result_dict["longitude"]
            item["latitude"] = result_dict["latitude"]
            # item["adcode"] = result_dict["adcode"]
            item['区'] = result_dict['区']
            break
    return item

def parse_gaode_json(json_text=""):
    return_dict = {
        "count": 0,
        "longitude": np.nan,
        "latitude": np.nan,
        "adcode": np.nan,
        "区": np.nan,
    }
    if 1 > len(json_text):
        return return_dict
    json_obj = json.loads(json_text)
    if json_obj is not None and "count" in json_obj.keys() and 0 < int(json_obj["count"]):
        if "geocodes" in json_obj.keys() and isinstance(json_obj["geocodes"], list) and 0 < len(json_obj['geocodes']):
            adcode = json_obj['geocodes'][0]['adcode']
            district = json_obj['geocodes'][0]['district']
            temp = json_obj['geocodes'][0]['location']
            temp_list = temp.split(',')
            if 1 < len(temp_list):
                longitude = temp_list[0]
                latitude = temp_list[1]
                return_dict['longitude'] = longitude
                return_dict['latitude'] = latitude
                return_dict['adcode'] = adcode
                return_dict["count"] = 1
                return_dict['区'] = district
    return return_dict






