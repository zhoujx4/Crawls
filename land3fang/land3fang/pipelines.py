# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exporters import JsonLinesItemExporter,CsvItemExporter
from datetime import datetime


class Land3FangPipeline(object):
    def __init__(self):
        self.json = open('D:\JC-JUN\land3fang\land3fang\spiders\output\land3fang_zpg_{}.json'.format(datetime.now().strftime('%Y-%m-%d')), 'ab')
        self.json_exporter = JsonLinesItemExporter(self.json, ensure_ascii=False, encoding='utf-8')
        self.csv = open('D:\JC-JUN\land3fang\land3fang\spiders\output\land3fang_zpg_{}.csv'.format(datetime.now().strftime('%Y-%m-%d')), 'ab')
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
