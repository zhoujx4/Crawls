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
from urllib import parse

from tt.extensions.commonfunctions import CommonScrapyPipelineClass

class Cnemc1Pipeline(object):
	
	root_path = ""
	overwrite_today = ""

	# dir, filename, folder
	crawled_dir = ""
	detail_html_dir = ""
	csv_file_path = None

	kafka_producer = None
	to_kafka = None
	kafka_topic = ""
	cluster_servers_for_spiders = []
	cluster_servers_for_kafka = []
		
	def init_self_attributes(self, spider):
		if self.root_path is None or 1 > len( self.root_path ):
			self.root_path = spider.settings.get( "PROJECT_PATH", default = None )
		if self.overwrite_today is None or 1 > len( self.overwrite_today ):
			self.overwrite_today = spider.settings.get( "OVERWRITE_TODAY", default = "" )
		if 1 > len( self.overwrite_today ):
			self.overwrite_today = datetime.datetime.now().strftime("%Y%m%d")

		# set all filenames, file paths, dir
		if 1 > len( self.crawled_dir ):
			self.crawled_dir = spider.settings.get( name='CRAWLED_DIR', default = "" )
		if 1 > len( self.detail_html_dir ):
			self.detail_html_dir = spider.settings.get( name="SAVED_DETAIL_HTML", default="" )
		if self.csv_file_path is None or 1 > len( self.csv_file_path ):
			self.csv_file_path = os.path.join( self.crawled_dir, f"{spider.name}_{self.overwrite_today}.csv" )

		if self.to_kafka is None:
			self.to_kafka = spider.settings.get( name="PIPELINE_TO_KAFKA", default = False )
		if 1 > len( self.kafka_topic ):
			self.kafka_topic = spider.name if hasattr( spider, "name" ) else ""
		if self.cluster_servers_for_spiders is None or 1 > len( self.cluster_servers_for_spiders ):
			self.cluster_servers_for_spiders = spider.settings.get( name="CLUSTER_SERVERS_FOR_SPIDERS", default = [] )
		if self.cluster_servers_for_kafka is None or 1 > len( self.cluster_servers_for_kafka ):
			self.cluster_servers_for_kafka = spider.settings.get( name="CLUSTER_SERVERS_FOR_KAFKA", default = [] )
		if socket.gethostname() in self.cluster_servers_for_spiders:
			self.kafka_producer = CommonScrapyPipelineClass.initialize_kafka( kafka_producer = self.kafka_producer, kafka_servers = self.cluster_servers_for_kafka, spider_obj = spider )
	
	def process_item(self, item, spider):
		"""
			revision: 20190730
		"""
		self.init_self_attributes( spider )

		page_type = ""
		for index, one in enumerate( item ):
			if "page_type" == one and 1 == len(item["page_type"]):
				page_type = str( item["page_type"][0] )
		excluded_list = ["page_type", ]
		key_list1, item_list1 = CommonScrapyPipelineClass.get_items_and_keys( item = item, excluded_key_list = excluded_list )
		index = -1
		content_dict = {}
		if "content" in key_list1 and "detailed" == page_type:
			index = key_list1.index( "content" )
			if -1 < index and index < len( item_list1 ):
				content_dict = eval(item_list1[index])
				item_list1.remove( item_list1[index] )
				key_list1.remove( "content" )

				keys = []
				items = []
				for key, value in content_dict.items():
					keys.append( key )
					items.append( value )
				key_list = keys + key_list1
				item_list = items + item_list1

				CommonScrapyPipelineClass.append_row( spider_obj = spider, key_list = key_list, item_list = item_list, csv_file_path_str = self.csv_file_path )
				if self.to_kafka and socket.gethostname() in self.cluster_servers_for_spiders:
					CommonScrapyPipelineClass.pipeline_to_kafka( spider_obj = spider, key_list = key_list, item_list = item_list, kafka_topic_str = self.kafka_topic, kafka_producer_obj = self.kafka_producer )
		elif "detailed" == page_type:
			error_msg = f"no content in key_list1 ({key_list1})"
			spider.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )

		return item

	def close_spider(self, spider = None):
		CommonScrapyPipelineClass.log_close_spider( spider_obj = spider )
