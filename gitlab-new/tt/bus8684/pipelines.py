# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import sys
import os
import datetime
import socket
import requests

from tt.extensions.commonfunctions import CommonScrapyPipelineClass

class Bus8684Pipeline(object):
	
	crawled_dir = ""
	csv_file_path = None

	kafka_producer = None
	to_kafka = None
	kafka_topic = ""
	cluster_servers_for_spiders = []
	cluster_servers_for_kafka = []
		
	def init_self_attributes(self, spider):
		today = datetime.datetime.now().strftime("%Y%m%d")
		if 1 > len( self.crawled_dir ):
			self.crawled_dir = spider.settings.get( name="CRAWLED_DIR", default = "" )
		if self.csv_file_path is None or 1 > len( self.csv_file_path ):
			self.csv_file_path = os.path.join( self.crawled_dir, f"{spider.name}{today}.csv" )

		if self.to_kafka is None:
			self.to_kafka = spider.settings.get( name="PIPELINE_TO_KAFKA", default = False )
		if 1 > len( self.kafka_topic ):
			self.kafka_topic = spider.name
		if self.cluster_servers_for_spiders is None or 1 > len( self.cluster_servers_for_spiders ):
			self.cluster_servers_for_spiders = spider.settings.get( name="CLUSTER_SERVERS_FOR_SPIDERS", default = [] )
		if self.cluster_servers_for_kafka is None or 1 > len( self.cluster_servers_for_kafka ):
			self.cluster_servers_for_kafka = spider.settings.get( name="CLUSTER_SERVERS_FOR_KAFKA", default = [] )

		if socket.gethostname() in self.cluster_servers_for_spiders:
			self.kafka_producer = CommonScrapyPipelineClass.initialize_kafka( kafka_producer = self.kafka_producer, kafka_servers = self.cluster_servers_for_kafka, spider_obj = spider )
	
	def process_item(self, item, spider):
		"""
			there are so many lat, and lng for one bus route (one item), therefore we do not request amap here.
		"""
		self.init_self_attributes( spider = spider )

		page_type = ""
		for index, one in enumerate( item ):
			if "page_type" == one and 1 == len(item["page_type"]):
				page_type = str( item["page_type"][0] )
				break
		
		excluded_list = ["page_type", ]
		key_list1, item_list1 = CommonScrapyPipelineClass.get_items_and_keys( item = item, excluded_key_list = excluded_list )

		if "detailed" == page_type:
			result_bool, key_list, item_list = CommonScrapyPipelineClass.extract_items_and_keys_from_content( raw_key_list=key_list1, raw_item_list = item_list1, content_field_name_str = "content")
			if result_bool:
				CommonScrapyPipelineClass.append_row( spider_obj = spider, key_list = key_list, item_list = item_list, csv_file_path_str = self.csv_file_path )
				if self.to_kafka and socket.gethostname() in self.cluster_servers_for_spiders:
					CommonScrapyPipelineClass.pipeline_to_kafka( spider_obj = spider, key_list = key_list, item_list = item_list, kafka_topic_str = self.kafka_topic, kafka_producer_obj = self.kafka_producer )
			else:
				spider.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, no content in key_list1 ({key_list1})" )

		return item

	def close_spider(self, spider = None):
		CommonScrapyPipelineClass.log_close_spider( spider_obj = spider )
