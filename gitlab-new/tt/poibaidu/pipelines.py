# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import time
import sys
import os
import json
import pandas as pd
import numpy as np
import datetime
import csv
import re
import random
import socket
import requests

import scrapy
from scrapy.exceptions import DropItem
from scrapy.utils.request import referer_str
from scrapy.loader import ItemLoader

# from poibaidu.items import PoibaiduItem # there is no need for this line!

class PoibaiduPipeline(object):
	
	overwrite_today = ""
	crawled_dir = ""
	csv_file_path = None

	kafka_producer = None
	to_kafka = None
	kafka_topic = ""
		
	def init_self_attributes(self, spider):
		self.overwrite_today = datetime.datetime.now().strftime("%Y%m%d")
		if 1 > len( self.crawled_dir ):
			self.crawled_dir = spider.settings.get( name="CRAWLED_DIR", default = "" )
		if self.csv_file_path is None or 1 > len( self.csv_file_path ):
			self.csv_file_path = os.path.join( self.crawled_dir, f"{spider.name}{self.overwrite_today}.csv" )
		if self.to_kafka is None:
			self.to_kafka = spider.settings.get( name="PIPELINE_TO_KAFKA", default = False )
		if 1 > len( self.kafka_topic ):
			self.kafka_topic = spider.name if hasattr( spider, "name" ) else ""
		if "entrobus28" == socket.gethostname():
			from kafka import KafkaProducer
			# for importing into hbase using Kafka
			if self.kafka_producer is None:
				self.kafka_producer = KafkaProducer(bootstrap_servers = "entrobus32:9092")
	
	def get_items_and_keys(self, item=None, excluded_list=[]):
		item_list = []
		all_keys = []
		if item is None:
			return all_keys, item_list
		for index, one in enumerate( item ):
			if one not in excluded_list:
				all_keys.append( one )
				if 0 == len(item[one]):
					item_list.append("")
				elif 1 == len(item[one]):
					item_list.append( item[one][0] )
				else:
					item_list.append( item[one] )
		return all_keys, item_list

	def process_item(self, item, spider):
		self.init_self_attributes( spider )

		page_type = ""
		for index, one in enumerate( item ):
			if "page_type" == one and 1 == len(item["page_type"]):
				page_type = str( item["page_type"][0] )
				break
		excluded_list = ["page_type", ]
		all_keys1, item_list1 = self.get_items_and_keys( item = item, excluded_list = excluded_list )
		index = -1
		content_dict = {}
		if "content" in all_keys1 and "json" == page_type:
			index = all_keys1.index( "content" )
			if -1 < index and index < len( item_list1 ):
				content_dict = eval(item_list1[index])
				item_list1.remove( item_list1[index] )
				all_keys1.remove( "content" )

				keys = []
				items = []
				for key, value in content_dict.items():
					keys.append( key )
					items.append( value )
				all_keys = keys + all_keys1
				item_list = items + item_list1
				self.append_row( spider = spider, all_keys = all_keys, item_list = item_list )
				if self.to_kafka and "entrobus28" == socket.gethostname():
					self.pipeline_to_kafka( spider = spider, all_keys = all_keys, item_list = item_list  )
		elif "json" == page_type:
			spider.logger.error( f"no content in all_keys1 ({all_keys1}) in Method process_item of Class QqhousePipeline. Exception = {ex}" )

		return item

	def append_row(self, spider = None, all_keys = [], item_list = [] ):
		try:
			if self.csv_file_path is None or 1 > len( self.csv_file_path ):
				spider.logger.error( f"missing filename qqhouse{self.overwrite_today}.csv or CRAWLED_DIR ({self.crawled_dir}) setting" )
			else:
				new_file = False
				if not os.path.isfile( self.csv_file_path ):
					new_file = True
				with open( self.csv_file_path, "a", encoding="utf-8", newline="") as f:
					writer = csv.writer(f)
					if new_file:
						writer.writerow( all_keys )
					writer.writerow( item_list )
		except Exception as ex:
			spider.logger.error( f"cannot write into file {self.csv_file_path}; content is: {item_list}; Exception = {ex}" )

	def pipeline_to_kafka( self, spider = None, all_keys = [], item_list = []  ):
		if 1 > len( self.kafka_topic ):
			spider.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, Exception: None == spider.name" )
			return False
		if 1 > len( all_keys ) or 1 > len( item_list ):
			spider.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, Exception: empty keys or empty values ({all_keys} or {item_list})" )
			return False
		if self.kafka_producer is None:
			spider.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, Exception: self.kafka_producer is None" )
			return False

		self.kafka_producer.send(self.kafka_topic, bytes( json.dumps( dict(zip( all_keys, item_list )) ), encoding="utf-8" ), timestamp_ms = int(time.time()*1000) )
		return True

	def close_spider(self, spider = None):
		now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		if spider is not None:
			spider.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, spider closes at {now}" )
