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

class FangesfPipeline(object):
	
	root_path = ""
	overwrite_today = ""

	# Gaode information
	base_gaode_url = "https://restapi.amap.com/v3/geocode/geo"
	key_list = [] # gaode keys
	city_name_dict = {}
	city_list = []
	district_list = []
	city_name_for_districts = ""
	save_every_response = None
	headers = {}

	# dir, filename, folder
	crawled_dir = ""
	detail_html_dir = ""
	gaode_json_dir = ""
	csv_file_path = None

	kafka_producer = None
	to_kafka = None
	kafka_topic = "fangesf" # do not use spider.name == fangesfpa
	cluster_servers_for_spiders = []
	cluster_servers_for_kafka = []
		
	def init_self_attributes(self, spider):
		if self.root_path is None or 1 > len( self.root_path ):
			self.root_path = spider.settings.get( "PROJECT_PATH", default = None )
		if self.overwrite_today is None or 1 > len( self.overwrite_today ):
			self.overwrite_today = spider.settings.get( "OVERWRITE_TODAY", default = "" )
		if 1 > len( self.overwrite_today ):
			self.overwrite_today = datetime.datetime.now().strftime("%Y%m%d")

		# Gaode information
		if 1 > len( self.key_list ):
			self.key_list = spider.settings.get( "AMAP_KEYS", default = [] )
		if 1 > len( self.city_name_dict ):
			self.city_name_dict = spider.settings.get( "CITY_NAME_DICT", default = {} )
		if 1 > len( self.city_list ):
			self.city_list = spider.settings.get( "CITY_LIST", default = [] )
		if 1 > len( self.district_list ):
			self.district_list = spider.settings.get( "DISTRICT_LIST", default = [] )
		if 1 > len( self.city_name_for_districts ):
			self.city_name_for_districts = spider.settings.get( "CITY_NAME_FOR_DISTRICTS", default = "" )
		if self.save_every_response is None:
			self.save_every_response = spider.settings.get( "SAVE_EVERY_RESPONSE", default = False )
		if 1 > len( self.headers ):
			self.headers = spider.settings.get( "DEFAULT_REQUEST_HEADERS", default = {} )

		# set all filenames, file paths, dir
		if 1 > len( self.crawled_dir ):
			self.crawled_dir = spider.settings.get( name='CRAWLED_DIR', default = "" )
		if 1 > len( self.detail_html_dir ):
			self.detail_html_dir = spider.settings.get( name="SAVED_DETAIL_HTML", default="" )
		if 1 > len( self.gaode_json_dir ):
			self.gaode_json_dir = spider.settings.get( name="SAVED_GAODE_JASON", default="" )
		if self.csv_file_path is None or 1 > len( self.csv_file_path ):
			self.csv_file_path = os.path.join( self.crawled_dir, f"fang_esf{self.overwrite_today}.csv" )

		if self.to_kafka is None:
			self.to_kafka = spider.settings.get( name="PIPELINE_TO_KAFKA", default = False )
		if self.cluster_servers_for_spiders is None or 1 > len( self.cluster_servers_for_spiders ):
			self.cluster_servers_for_spiders = spider.settings.get( name="CLUSTER_SERVERS_FOR_SPIDERS", default = [] )
		if self.cluster_servers_for_kafka is None or 1 > len( self.cluster_servers_for_kafka ):
			self.cluster_servers_for_kafka = spider.settings.get( name="CLUSTER_SERVERS_FOR_KAFKA", default = [] )
		if socket.gethostname() in self.cluster_servers_for_spiders:
			self.kafka_producer = CommonScrapyPipelineClass.initialize_kafka( kafka_producer = self.kafka_producer, kafka_servers = self.cluster_servers_for_kafka, spider_obj = spider )
	
	def switch_city_name(self, city_name = "", spider = None):
		"""
			switch a fang.com city name (city_name ) to a Amap.com city name
			modified on 20190624, changed self.city_names to self.city_name_dict
		"""
		if not isinstance(city_name, str) or 1 > len( self.city_name_dict ):
			return ""

		if city_name in self.city_name_dict.keys():
			return self.city_name_dict[ city_name ]
		error_msg = f"cannot find city / district name {city_name}"
		spider.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		return ""

	def save_reponsed_json_file(self, apt_id = "", response = "", spider = None ):
		if 1 > len( apt_id ) or 1 > len( response ):
			return False
		json_filename = f"random{ random.randint(10000,99999) }"
		if re.match( r'^(\d)+$', apt_id ):
			json_filename = apt_id
		json_filepath = os.path.join( self.gaode_json_dir, f"{json_filename}.json" )
		try:
			if isinstance( response, str ):
				with open( json_filepath, "a", encoding="utf-8" ) as f: # newline="", errors="ignore"
					f.write( response )
			elif isinstance( response, bytes ):
				with open( json_filepath, "wb", encoding="utf-8" ) as f: # overwrite any previous responses # do not know if encoding="utf-8" good with "b"
					f.write(response)
			else:
				with open( json_filepath, "wb", encoding="utf-8" ) as f: # overwrite any previous responses
					f.write( bytes(response) )
		except Exception as ex:
			error_msg = f"fail to write {json_filepath}. Exception = {ex}"
			spider.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
	
	def extract_community_name(self, content_dict = {}):
		community_name = ""
		if content_dict is None or 1 > len( content_dict ):
			return community_name

		if "location" in content_dict.keys():
			if "小区" in content_dict["location"]:
				temp = content_dict["location"]["小区"]
				if -1 < temp.find('\r'):
					temp_list = temp.split('\r')
					if 0 < len( temp_list ):
						temp = temp_list[0]
				if 0 < len( temp ):
					community_name = temp

		if 1 > len( community_name ) and "community" in content_dict.keys():
			community = content_dict["community"]
			if isinstance(community, dict) and "title" in community.keys():
				title = community["title"]
				if -1 < title.find("小区信息"):
					title = title.replace("小区信息", "")
				if 0 < len( title ):
					community_name = title
		return community_name

	def get_city_or_district_name_from_url(self, url = ""):
		"""
			there is no need to extract district name. we ONLY use city for requesting Gaode
			and we changed CITY_NAMES list to CITY_NAME_DICT
		"""
		if not isinstance( url, str ) or 1 > len( url ):
			return ""
		url_obj = parse.urlparse(url)
		if -1 < url_obj.netloc.find("esf.fang.com"):
			temp_list = url_obj.netloc.split(".")
			return temp_list[0] if 0 < len( temp_list ) and 0 < len( temp_list[0] ) else ""
		return ""

	def process_item(self, item, spider):
		"""
			todo: some parts of this method can be moved to commonfunctions.py
		"""
		self.init_self_attributes( spider )

		random_key = random.randint( 0, len(self.key_list) - 1 )
		account = self.key_list[ random_key ]

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
				content_dict["longitude"] = np.nan
				content_dict["latitude"] = np.nan
				content_dict["adcode"] = np.nan

				# request Gaode here
				if isinstance(item["url"], list):
					url_str = str(item["url"][0])
				elif isinstance( item["url"], str ):
					url_str = item["url"]
				city_name_fang = self.get_city_or_district_name_from_url( url = url_str )
				if 0 < len( city_name_fang ):
					city_name_amap = self.switch_city_name(city_name = city_name_fang, spider = spider )
					community_name = self.extract_community_name( content_dict = content_dict )
					spider.logger.info( f"requesting Gaode using community name {community_name}")
					if 0 < len( community_name ):
						result_dict = {}
						params = {
							"key": account,
							"address": str( CommonScrapyPipelineClass.clean_addr( text = community_name ) ),
							"city": city_name_amap,
						}
						try:
							# 20190621发现爬取佛山的时候因为DNS解析失败而丢失了14条记录。这里增加代码，记录再次丢失。
							# socket.gaierror: [Errno -3] Temporary failure in name resolution
							response = requests.get( self.base_gaode_url, headers= self.headers, params=params )
							if 200 == response.status_code:
								if self.save_every_response is not None and self.save_every_response:
									self.save_reponsed_json_file(apt_id = content_dict["apt_id"], response = response.text, spider = spider )
								result_dict = CommonScrapyPipelineClass.parse_gaode_json( json_text = response.text )
								if 0 < (result_dict["count"]):
									content_dict["longitude"] = result_dict["longitude"]
									content_dict["latitude"] = result_dict["latitude"]
									content_dict["adcode"] = result_dict["adcode"]
						except Exception as ex:
							spider.logger.error( f"requests or other errors. Exception = {ex}")
				
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
