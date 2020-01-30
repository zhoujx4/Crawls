# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exporters import JsonLinesItemExporter,CsvItemExporter
import os
from datetime import datetime

PROJECT_PATH = os.getcwd()
PROJECT_PATH = os.path.join(PROJECT_PATH, "output")

class BsrentPipeline(object):
    def __init__(self):
        self.path = PROJECT_PATH
        self.json = open(os.path.join(self.path, 'Bsrent{}.json'.format(datetime.now().strftime('%Y-%m-%d'))), 'ab')
        self.json_exporter = JsonLinesItemExporter(self.json, ensure_ascii=False, encoding='utf-8')
        self.csv = open(os.path.join(self.path, 'Bsrent{}.csv'.format(datetime.now().strftime('%Y-%m-%d'))), 'ab')
        self.csv_exporter = CsvItemExporter(self.csv, encoding='utf-8')

    def open_spider(self, spider):
        print("爬虫开始了")


    def process_item(self, item, spider):
        self.json_exporter.export_item(item)
        self.csv_exporter.export_item(item)
        return item

    def close_spider(self, spider):
        self.json.close()
        self.csv.close()

        print("爬虫结束了")

class BssalePipeline(object):
    def __init__(self):
        self.path = PROJECT_PATH
        self.json = open(os.path.join(self.path, 'Bssale{}.json'.format(datetime.now().strftime('%Y-%m-%d'))), 'ab')
        self.json_exporter = JsonLinesItemExporter(self.json, ensure_ascii=False, encoding='utf-8')
        self.csv = open(os.path.join(self.path, 'Bssale{}.csv'.format(datetime.now().strftime('%Y-%m-%d'))), 'ab')
        self.csv_exporter = CsvItemExporter(self.csv, encoding='utf-8')

    def open_spider(self, spider):
        print("爬虫开始了")

    def process_item(self, item, spider):
        self.json_exporter.export_item(item)
        self.csv_exporter.export_item(item)
        return item

    def close_spider(self, spider):
        self.json.close()
        self.csv.close()

        print("爬虫结束了")

class EsfrentPipeline(object):
    def __init__(self):
        self.path = PROJECT_PATH
        self.json = open(os.path.join(self.path, 'Esfrent{}.json'.format(datetime.now().strftime('%Y-%m-%d'))), 'ab')
        self.json_exporter = JsonLinesItemExporter(self.json, ensure_ascii=False, encoding='utf-8')
        self.csv = open(os.path.join(self.path, 'Esfrent{}.csv'.format(datetime.now().strftime('%Y-%m-%d'))), 'ab')
        self.csv_exporter = CsvItemExporter(self.csv, encoding='utf-8')

    def open_spider(self, spider):
        print("爬虫开始了")


    def process_item(self, item, spider):
        self.json_exporter.export_item(item)
        self.csv_exporter.export_item(item)
        return item

    def close_spider(self, spider):
        self.json.close()
        self.csv.close()

        print("爬虫结束了")

class EsfsalePipeline(object):
    def __init__(self):
        self.path = PROJECT_PATH
        self.json = open(os.path.join(self.path, 'Esfsale{}.json'.format(datetime.now().strftime('%Y-%m-%d'))), 'ab')
        self.json_exporter = JsonLinesItemExporter(self.json, ensure_ascii=False, encoding='utf-8')
        self.csv = open(os.path.join(self.path, 'Esfsale{}.csv'.format(datetime.now().strftime('%Y-%m-%d'))), 'ab')
        self.csv_exporter = CsvItemExporter(self.csv, encoding='utf-8')

    def open_spider(self, spider):
        print("爬虫开始了")

    def process_item(self, item, spider):
        self.json_exporter.export_item(item)
        self.csv_exporter.export_item(item)
        return item

    def close_spider(self, spider):
        self.json.close()
        self.csv.close()

        print("爬虫结束了")