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

class Shop58Pipeline(object):
	
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
			self.csv_file_path = os.path.join( self.crawled_dir, f"shop58_{self.overwrite_today}.csv" )

		if self.to_kafka is None:
			self.to_kafka = spider.settings.get( name="PIPELINE_TO_KAFKA", default = False )
		if 1 > len( self.kafka_topic ):
			self.kafka_topic = spider.name if hasattr( spider, "name" ) else ""
		if "entrobus28" == socket.gethostname():
			from kafka import KafkaProducer
			if self.kafka_producer is None:
				self.kafka_producer = KafkaProducer(bootstrap_servers = "entrobus32:9092")
	
	def check_city_name(self, city_name = "", spider = None):
		if isinstance(city_name, str):
			if 1 > len( self.city_names) or 1 > len( self.city_list ):
				return ""
			try:
				index = self.city_list.index( city_name )
				if index > len( self.city_names ) - 1:
					return ""
				return self.city_names[index]
			except Exception as ex:
				error_msg = f"cannot find city name {city_name}. Exception is: {ex}"
				spider.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
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

	def save_reponsed_json_file(self, shop_id = "", response = "", spider = None ):
		if 1 > len( shop_id ) or 1 > len( response ):
			return False
		json_filename = f"random{ random.randint(10000,99999) }"
		if re.match( r'^(\d)+$', shop_id ):
			json_filename = shop_id
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
	
	def extract_address(self, content_dict = {}):
		address = ""
		if content_dict is None or 1 > len( content_dict ):
			return address
		if "address" in content_dict.keys():
			address = content_dict["address"]
		return address

	def process_item(self, item, spider):
		self.init_self_attributes( spider )

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
					city_name = self.check_city_name(city_name = city_name, spider = spider )
					address = self.extract_address( content_dict = content_dict )
					spider.logger.info( f"requesting Gaode using address {address}")
					if 0 < len( address ):
						result_dict = {}
						params = {
							"key": account,
							"address": str( self.clean_addr(address) ),
							"city": city_name,
						}
						response = requests.get( self.base_gaode_url, headers= self.headers, params=params )
						if 200 == response.status_code:
							if self.save_every_response is not None and self.save_every_response:
								self.save_reponsed_json_file(shop_id = content_dict["shop_id"], response = response.text, spider = spider )
							result_dict = self.parse_gaode_json( response.text )
							if 0 < (result_dict["count"]):
								content_dict["longitude"] = result_dict["longitude"]
								content_dict["latitude"] = result_dict["latitude"]
								content_dict["adcode"] = result_dict["adcode"]
				keys = []
				items = []
				for key, value in content_dict.items():
					keys.append( key )
					items.append( value )
				all_keys = keys + all_keys1
				item_list = items + item_list1
				self.append_row( all_keys = all_keys, item_list = item_list, spider = spider )
				if self.to_kafka and "entrobus28" == socket.gethostname():
					self.pipeline_to_kafka( spider = spider, all_keys = all_keys, item_list = item_list  )
		elif "detailed" == page_type:
			error_msg = f"no content in all_keys1 ({all_keys1})"
			spider.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )

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

	def append_row(self, all_keys = [], item_list = [], spider = None ):
		try:
			if self.csv_file_path is None or 1 > len( self.csv_file_path ):
				spider.logger.error( f"missing filename shop58_{self.overwrite_today}.csv or CRAWLED_DIR ({self.crawled_dir}) setting" )
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
			spider.logger.info( f"Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__} is called at {now}" )
