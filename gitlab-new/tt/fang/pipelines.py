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

from tt.extensions.commonfunctions import CommonScrapyPipelineClass

class FangPipeline(object):
	
	root_path = ""
	overwrite_today = ""

	# Gaode information
	base_gaode_url = "https://restapi.amap.com/v3/geocode/geo"
	key_list = [] # gaode keys
	city_names = []
	city_list = []
	save_every_response = None
	headers = {}

	# dir, filename, folder
	crawled_dir = ""
	detail_html_dir = ""
	gaode_json_dir = ""
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

		# Gaode information
		if 1 > len( self.key_list ):
			self.key_list = spider.settings.get( "AMAP_KEYS", default = [] )
		if 1 > len( self.city_names ):
			self.city_names = spider.settings.get( "CITY_NAMES", default = [] )
		if 1 > len( self.city_list ):
			self.city_list = spider.settings.get( "CITY_LIST", default = [] )
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
			self.csv_file_path = os.path.join( self.crawled_dir, f"fang_zu{self.overwrite_today}.csv" )

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
	
	def check_city_name(self, city_name):
		if isinstance(city_name, str):
			if 1 > len( self.city_names) or 1 > len( self.city_list ):
				return ""
			try:
				index = self.city_list.index( city_name )
				if index > len( self.city_names ) - 1:
					return ""
				return self.city_names[index]
			except Exception as ex:
				print( f'cannot find city name {city_name}. Exception is: {ex}' )
				return ""
		return ""

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

	def parse_gaode_json(self, json_text = ""):
		return_dict = {
			"count": 0,
			"longitude": np.nan,
			"latitude": np.nan,
			"adcode": np.nan,
		}
		if 1 > len( json_text ):
			return return_dict
		json_obj = json.loads( json_text )
		if json_obj is not None and "count" in json_obj.keys() and 0 < int( json_obj["count"] ):
			if "geocodes" in json_obj.keys() and isinstance(json_obj["geocodes"], list) and 0 < len( json_obj['geocodes'] ):
				adcode = json_obj['geocodes'][0]['adcode']
				temp = json_obj['geocodes'][0]['location']
				temp_list = temp.split(',')
				if 1 < len( temp_list ):
					longitude = temp_list[0]
					latitude = temp_list[1]
					return_dict['longitude'] = longitude
					return_dict['latitude'] = latitude
					return_dict['adcode'] = adcode
					return_dict["count"] = 1
		return return_dict

	def save_reponsed_json_file(self, rent_id = "", response = "" ):
		if 1 > len( rent_id ) or 1 > len( response ):
			return False
		temp_list = rent_id.split("_")
		if 1 > len( temp_list ):
			return False
		json_filename = f"random{ random.randint(10000,99999) }"
		for one in temp_list:
			if re.match( r'^(\d)+$', one ):
				json_filename = one
				break
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
			print( f"Exception happened while writing to {json_filepath}. Exception = {ex}" )
			

	def process_item(self, item, spider):
		self.init_self_attributes( spider = spider )

		random_key = random.randint( 0, len(self.key_list) - 1 )
		account = self.key_list[ random_key ]

		page_type = ""
		for index, one in enumerate( item ):
			if "page_type" == one and 1 == len(item["page_type"]):
				page_type = str( item["page_type"][0] )
		excluded_list = ["page_type", ]
		all_keys1, item_list1 = self.get_items_and_keys( item = item, excluded_list = excluded_list )
		index = -1
		content_dict = {}
		if "content" in all_keys1 and "detailed" == page_type:
			index = all_keys1.index( "content" )
			if -1 < index and index < len( item_list1 ):
				content_dict = eval(item_list1[index])
				item_list1.remove( item_list1[index] )
				all_keys1.remove( "content" )
				content_dict["longitude"] = np.nan
				content_dict["latitude"] = np.nan
				content_dict["adcode"] = np.nan

				# request Gaode here
				if isinstance(item["url"], list):
					temp_list = str(item["url"][0]).replace("https://", "")
				elif isinstance( item["url"], str ):
					temp_list = item["url"].replace("https://", "")
				temp_list = temp_list.split(".")
				city_name = temp_list[0] if 0 < len( temp_list ) and 0 < len( temp_list[0] ) else ""
				if 0 < len( city_name ):
					city_name = self.check_city_name(city_name)
					three_requests_for_tryout = ["location", "address", ]
					for one_tryout in three_requests_for_tryout:
						if one_tryout in content_dict.keys():
							result_dict = {}
							params = {
								"key": account,
								"address": str( self.clean_addr(content_dict[one_tryout]) ),
								"city": city_name,
							}
							response = requests.get( self.base_gaode_url, headers= self.headers, params=params )
							if 200 == response.status_code:
								if self.save_every_response is not None and self.save_every_response:
									self.save_reponsed_json_file(rent_id = content_dict["rent_id"], response = response.text )
								result_dict = self.parse_gaode_json( response.text )
								if 0 < (result_dict["count"]):
									content_dict["longitude"] = result_dict["longitude"]
									content_dict["latitude"] = result_dict["latitude"]
									content_dict["adcode"] = result_dict["adcode"]
									break
				keys = []
				items = []
				for key, value in content_dict.items():
					keys.append( key )
					items.append( value )
				key_list = keys + all_keys1
				item_list = items + item_list1

				CommonScrapyPipelineClass.append_row( spider_obj = spider, key_list = key_list, item_list = item_list, csv_file_path_str = self.csv_file_path )
				if self.to_kafka and socket.gethostname() in self.cluster_servers_for_spiders:
					CommonScrapyPipelineClass.pipeline_to_kafka( spider_obj = spider, key_list = key_list, item_list = item_list, kafka_topic_str = self.kafka_topic, kafka_producer_obj = self.kafka_producer )
		elif "detailed" == page_type:
			spider.logger.error( f"no content in all_keys1 ({all_keys1}) in Method process_item of Class FangPipeline. Exception = {ex}" )

		return item

	def clean_addr(self, text):
		"""
		return string before (, *, or （
		"""
		if isinstance(text, str):
			text = text.strip('*')
			if -1 < text.find('（'):
				temp = text.split('（')
				if 0 < len( temp ):
					text = temp[0]
			if -1 < text.find('('):
				temp = text.split('(')
				if 0 < len( temp ):
					text = temp[0]
			if -1 < text.find('*'):
				temp = text.split('*')
				if 0 < len( temp ):
					text = temp[0]
		return text

	def close_spider(self, spider = None):
		CommonScrapyPipelineClass.log_close_spider( spider_obj = spider )
