# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import Selector
import csv
import re
import sys
import os
import datetime
import time
import random
import json
import numpy as np
import math
import copy
import socket
from urllib import parse

from scrapy.loader import ItemLoader
from scrapy.http import TextResponse

from tt.extensions.commonfunctions import CommonClass
from tt.extensions.commonfunctions import CommonScrapyPipelineClass
from traffic.items import TrafficItem

class FileFormatException(Exception):
	def __init__(self):
		Exception.__init__(self)

class TrafficSpider(scrapy.Spider):
	"""
		sys.exit code == 1 # missing AMAP_KEYS
		sys.exit code == 2 # missing INPUT_XY_FILE_PATH
		sys.exit code == 3 # fail to generate self.rectangle_list
		sys.exit code == 4 # self.rectangle_list have wrong length
	"""
	name = "traffic"
	
	root_path = ""
	log_dir = ""
	xy_response_log_file_name = ""
	city_or_area_name = ""
	# debug = False
	# save_every_response = False
	crawled_dir = ""
	json_dir = ""
	output_folder_name = ""
	output_file_format = "json"
	base_uri = ""
	run_purpose = None
	overwrite_today = ""
	custom_settings = CommonClass.get_custom_settings_dict( spider=name )

	# crontab will start a new process in every 6 hours; therefore in 1 day, the crontab will start 4 times
	# 5 minute between 2 adjacent reqests
	# the followings will be inititated in every 6 hours
	maximal_requests_of_one_crontab_process = 71
	interval_between_requests = 300
	amap_key_list = []
	amap_key_pointer = 0
	request_counter = 0 # from 0 to 71
	request_number_per_batch = 405 # there are 405 requests in every 5 minutes
	# request_number_per_batch = 10
	rectangle_list = [] # items looks like "113.267593,23.358604;113.337613,23.412658", it equals to list( self.edges_of_center_xy_dict.keys() )
	edges_of_center_xy_dict = {} # key looks like "113.267593,23.358604;113.337613,23.412658" and item looks like "113.737414,22.543564"
	xy_seen_dict = {} # key looks like "113.737414,22.543564" and item looks like 23
	xy_seen_updated_bool = False

	# the followings will be initiated in every 5 minutes
	last_batch_request_list = []
	last_batch_request_timestamp_float = 0.0 # if good response returned, then we use self.last_batch_request_timestamp_float
	urls = []

	def get_next_amap_key(self):
		self.amap_key_pointer -= 1
		if 0 > self.amap_key_pointer:
			self.amap_key_pointer = len(self.amap_key_list) - 1
		return self.amap_key_list[self.amap_key_pointer]

	def get_one_batch_urls(self):
		"""
		https://restapi.amap.com/v3/traffic/status/rectangle?level=6&extensions=all&output=json&rectangle=113.2675927679,23.3586043241;113.3376127679,23.4126583781&key=4ebb849f151dddb3e9aab7abe6e344e2
		"""
		self.urls = []
		self.last_batch_request_list = []
		query_dict = {
			"level": 6,
			"extensions": "all",
			"output": "json",
			"key": self.get_next_amap_key(),
		}
		for one_retangle in self.rectangle_list:
			query_dict["rectangle"] = one_retangle
			self.last_batch_request_list.append(one_retangle)
			self.urls.append( f"{self.base_uri}?{parse.urlencode(query_dict)}" )

		self.last_batch_request_timestamp_float = time.time()
		return self.urls

	def generate_one_rectange(self, center_xy_str = ""):
		if not isinstance( center_xy_str, str) or 1 > len( center_xy_str ):
			return ""
		xy_list = center_xy_str.split(",")
		x = float( xy_list[0] )
		y = float( xy_list[1] )
		# edge = 3.0 km
		# lat_delta = 0.009009009*edge = 0.027027027
		# 赤道长度40075公里；北纬23度每一经度长40075 * sin(90-23) / 360 = 36889.23 / 360 = 102.47008889公里
		# lng_delta = 0.009759*edge = 0.0292768
		return "%.6f,%.6f;%.6f,%.6f" % ( x - 0.0292768, y - 0.027027027, x + 0.0292768, y + 0.027027027 )

	def init_self_rectangles(self):
		if isinstance( self.rectangle_list, list ) and 0 < len( self.rectangle_list ):
			return self.rectangle_list
		
		try:
			with open( self.input_xy_file_path, "r", encoding="utf-8" ) as xy_file:
				overall_list = xy_file.readlines()
				for index,one_xy in enumerate(overall_list):
					xy_list = one_xy.split(",")
					if isinstance( xy_list, list) and 2 == len( xy_list ):
						center_xy = "%.6f,%.6f" % ( float(xy_list[0]), float(xy_list[1]) )
						rect_str = self.generate_one_rectange( center_xy_str = center_xy )
						self.rectangle_list.append( rect_str )
						self.edges_of_center_xy_dict[rect_str] = center_xy
		except Exception as ex:
			self.logger.error( f"cannot read xy_list file ({xy_file_path}). Exception = {ex}" )
			sys.exit(3)
		else:
			return self.rectangle_list

	def init_self_xy_response_log(self):
		log_file_path = os.path.join( self.log_dir, self.xy_response_log_file_name )
		try:
			with open( log_file_path, "r", encoding="utf-8" ) as xy_log_file:
				overall_list = xy_log_file.readlines()
				for index, one_xy in enumerate(overall_list):
					xy_list = one_xy.split(",")
					if isinstance( xy_list, list) and 3 == len( xy_list ):
						center_xy = "%.6f,%.6f" % ( float(xy_list[0]), float(xy_list[1]) )
						self.xy_seen_dict[center_xy] = int(xy_list[2])
		except Exception as ex:
			self.logger.error( f"cannot read historical xy_log_file ({log_file_path}). Exception = {ex}" )
			# do not sys.exit(3) here
			self.xy_seen_updated_bool = True
			return False
		else:
			return True

	def init_self_attributes(self):
		self.root_path = self.settings.get( "PROJECT_PATH" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )
		self.xy_response_log_file_name = self.settings.get( name="XY_RESPONSE_LOG_FILE_NAME", default="" )
		self.city_or_area_name = self.settings.get( name="CITY_OR_AREA_NAME", default="" )
		# self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		# self.save_every_response = self.settings.get( name = "SAVE_EVERY_RESPONSE", default=False )
		self.crawled_dir = self.settings.get( name="CRAWLED_DIR", default = "" )
		self.json_dir = self.settings.get( name="SAVED_JSON", default="" )
		self.output_folder_name = self.settings.get( name="OUTPUT_FOLDER_NAME", default="" )
		self.base_uri = self.settings.get( name = "BASE_URI", default="" )
		self.run_purpose = self.settings.get( name = "RUN_PURPOSE", default=None )
		self.overwrite_today = self.settings.get( name = "OVERWRITE_TODAY", default="" )

		self.maximal_requests_of_one_crontab_process = self.settings.get( name="MAXIMAL_REQUESTS_OF_ONE_CRONTAB_PROCESS", default=71 )
		self.interval_between_requests = self.settings.get( name="INTERVAL_BETWEEN_REQUESTS", default=300 )
		self.amap_key_list = self.settings.get( name = "AMAP_KEYS", default=[] )
		if 1 > len( self.amap_key_list ):
			self.logger.error( f"self.amap_key_list is empty" )
			sys.exit(1)
		self.input_xy_file_path = self.settings.get( name = "INPUT_XY_FILE_PATH", default="" )
		if not isinstance( self.input_xy_file_path, str ) or 1 > len( self.input_xy_file_path ):
			self.logger.error( f"missing INPUT_XY_FILE_PATH" )
			sys.exit(2)

		self.init_self_rectangles()
		if self.request_number_per_batch != len( self.rectangle_list ):
			self.logger.error( f"self.rectangle_list length shall be {self.request_number_per_batch}" )
			sys.exit(4)

		self.init_self_xy_response_log()

	def check_dirs_and_files(self):
		if not os.path.isdir( self.crawled_dir ):
			os.makedirs( self.crawled_dir )
		if not os.path.isdir( self.json_dir ):
			os.makedirs( self.json_dir )

	def start_requests(self):
		self.init_self_attributes()
		self.check_dirs_and_files()

		if "INITIALIZE_AMAP_XY" == self.run_purpose:
			"""
				生成xy坐标文件需要将山上、水面上的坐标去除掉。另外20190703发现广东东莞是没有数据的。要将广东东莞的数据删除掉
			"""
			xy_file_name = "data4cities_bd09.txt"
			xy_file_path = os.path.join( self.root_path, self.name, xy_file_name )
			try:
				with open( xy_file_path, "r", encoding="utf-8" ) as f:
					overall_lines = f.readlines()
					overall_list = overall_lines[0].split(";")
					for index,one_xy in enumerate(overall_list):
						xy_list = one_xy.split(",")
						if isinstance( xy_list, list) and 2 == len( xy_list ):
							xy = "%.6f,%.6f" % ( float(xy_list[0]), float(xy_list[1]) )
							one_url = f"https://restapi.amap.com/v3/assistant/coordinate/convert?locations={xy}&coordsys=baidu&output=json&key=4ebb849f151dddb3e9aab7abe6e344e2"
							meta_dict = {
								"x": float( xy_list[0] ),
								"y": float( xy_list[1] ),
								"index": index,
							}
							yield scrapy.Request( url=one_url, callback=self.initialize_amap_xy, meta = meta_dict, dont_filter = True )
			except Exception as ex:
				urls = []
				self.logger.error( f"cannot read xy_list file ({xy_file_path}). Exception = {ex}" )
		elif "READ_JSON_AND_WRITE_CSV" == self.run_purpose:
			one_url = "https://blog.csdn.net/qq_37193537/article/details/78987949"
			callback_func = self.read_json_and_parse
			yield scrapy.Request( url=one_url, callback=callback_func, dont_filter = True )
		else:
			self.get_one_batch_urls()
			meta_dict = {
				# we use self.last_batch_request_timestamp_float
				"redo_counter": 0,
			}
			for index, one_url in enumerate( self.urls ):
				meta_dict["center_xy_index"] = index
				self.logger.info( f"{index}: requesting {one_url} ")
				yield scrapy.Request( url=one_url, callback=self.parse_json, meta = meta_dict, dont_filter = True )

	def initialize_amap_xy(self, response):
		if response is None or not hasattr(response, "body") or not hasattr( response, "url" ) or not hasattr( response, "meta"):
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, bad response object" )
			return None
		meta_dict = response.meta
		bd09xy = "%.6f,%.6f" % ( meta_dict["x"], meta_dict["y"] )
		index = meta_dict["index"]
		json_dict = json.loads( response.body )
		if "status" not in json_dict.keys() or "locations" not in json_dict.keys() or 1 != int( json_dict["status"] ):
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, bad response status" )
			return None
		if not isinstance( json_dict["locations"], str ) or 1 > len( json_dict["locations"] ):
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, bad response locations" )
			return None
		amap_xy = json_dict["locations"]
		this_row = f"{index}:{bd09xy}==>{amap_xy}"
		new_xy_file_name = "data4cities_amap.txt"
		new_xy_log_file_name = "bd09to_amap.log"
		new_xy_log_file_name = os.path.join( self.root_path, self.name, new_xy_log_file_name )
		new_xy_file_name = os.path.join( self.root_path, self.name, new_xy_file_name )
		CommonScrapyPipelineClass.append_row( spider_obj = self, key_list = ["xy"], item_list = [amap_xy], csv_file_path_str = new_xy_file_name )
		CommonScrapyPipelineClass.append_row( spider_obj = self, key_list = ["xy"], item_list = [this_row], csv_file_path_str = new_xy_log_file_name )

	def read_json_and_parse(self, response):
		self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, todo..." )

	def check_trafficinfo_dict(self, trafficinfo_dict = {}, status_int = -1, infocode_int = -1, center_xy_index_int = -1 ):
		"""
			有可能得到下面的空结果；这个时候需要比对历史记录
			{"status":"1","info":"OK","infocode":"10000","trafficinfo":{"description":[],"evaluation":{"expedite":[],"congested":[],"blocked":[],"unknown":[],"status":[],"description":[]},"roads":[]}}
		"""
		if not isinstance(trafficinfo_dict, dict) or 1 > len( trafficinfo_dict ):
			return False
		
		if 1 != status_int or 10000 != infocode_int:
			return False

		edges = self.rectangle_list[center_xy_index_int] if center_xy_index_int in range( len(self.rectangle_list) ) else ""
		center_xy = self.edges_of_center_xy_dict[edges] if edges in self.edges_of_center_xy_dict.keys() else ""
		# if "roads" not in trafficinfo_dict.keys() or not isinstance( trafficinfo_dict["roads"], list ) or 1 > len( trafficinfo_dict["roads"] ):
			# 比对历史记录
			# if center_xy in self.xy_seen_dict.keys() and 0 == int(self.xy_seen_dict[center_xy]):
			# 	return True # 0表示该xy已经请求过3次，都返回空
			# elif center_xy in self.xy_seen_dict.keys() and 0 > int(self.xy_seen_dict[center_xy]):
			# 	if -3 == int():
			# 		self.xy_seen_dict[center_xy] = 0 # -1, -2, -3分别表示第1、2、3次请求返回空
			# 	else:
			# 		self.xy_seen_dict[center_xy] -= 1
			# 	self.xy_seen_updated_bool = True
			# elif center_xy not in self.xy_seen_dict.keys():
			# 	self.xy_seen_dict[center_xy] = -1
			# 	self.xy_seen_updated_bool = True
			# return False
			# 经过测试，上述方案会产生大量请求

		if center_xy not in self.xy_seen_dict.keys() or len(trafficinfo_dict["roads"]) > int(self.xy_seen_dict[center_xy]):
			self.xy_seen_dict[center_xy] = len(trafficinfo_dict["roads"])
			self.xy_seen_updated_bool = True
		return True

	def parse_json(self, response):
		status, infocode, message, result_dict = self.save_json( response = response, page_type = "json" )
		now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		meta_dict = response.meta
		center_xy_index = int(meta_dict["center_xy_index"]) if "center_xy_index" in meta_dict.keys() else -1

		if self.check_trafficinfo_dict( trafficinfo_dict = result_dict, status_int = status, infocode_int = infocode, center_xy_index_int = center_xy_index ):
			loader = ItemLoader( item = TrafficItem(), response = response )
			loader = self.load_items_into_loader( loader = loader, text = result_dict, url = response.url, now = now )
			yield loader.load_item()
		else:
			edges = self.rectangle_list[center_xy_index] if center_xy_index in range( len(self.rectangle_list) ) else ""
			center_xy = self.edges_of_center_xy_dict[edges] if edges in self.edges_of_center_xy_dict.keys() else ""
			center_xy_index = -1
			error_msg = f"redo request from {response.url} for {center_xy} because status == {status}, infocode == {infocode}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			meta_dict["redo_counter"] += 1
			yield scrapy.Request( url= response.url, callback=self.parse_json, meta = meta_dict, dont_filter = True )
		
		if -1 < center_xy_index:
			received_all_reponses_per_batch_bool = self.check_this_center_xy(center_xy_index_int = center_xy_index)
			print( f"received_all_reponses_per_batch_bool == {received_all_reponses_per_batch_bool}; center_xy_index = {center_xy_index}" )

			# get data again after 5 minutes
			if self.request_counter < self.maximal_requests_of_one_crontab_process and received_all_reponses_per_batch_bool:
				while( self.check_time_interval() ):
					time.sleep(10)
				
				self.request_counter += 1
				now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
				self.logger.info( f" requesting amap at {now} ( {self.request_counter} of { self.maximal_requests_of_one_crontab_process } )")
				self.get_one_batch_urls()
				meta_dict = {
					"redo_counter": 0,
				}
				for index, one_url in enumerate( self.urls ):
					meta_dict["center_xy_index"] = index
					self.logger.info( f"{index}: requesting {one_url} ")
					yield scrapy.Request( url=one_url, callback=self.parse_json, meta = meta_dict, dont_filter = True )

	def check_time_interval( self ):
		if time.time() - self.last_batch_request_timestamp_float > float(self.interval_between_requests):
			return False
		return True

	def check_this_center_xy(self, center_xy_index_int = -1):
		if center_xy_index_int not in range( len(self.rectangle_list) ):
			return True

		# 4 minutes have passed, just return True
		if time.time() - self.last_batch_request_timestamp_float > 240.0:
			temp_list = []
			for one_edge in self.last_batch_request_list:
				if one_edge in self.edges_of_center_xy_dict.keys():
					temp_list.append( self.edges_of_center_xy_dict[one_edge])
			self.logger.error( f"after 4 minutes, there are still {len(self.last_batch_request_list)} waiting for response: {temp_list} " )
			return True

		# remove current preset_route
		edges = self.rectangle_list[center_xy_index_int] if center_xy_index_int in range( len(self.rectangle_list) ) else ""
		if edges in self.last_batch_request_list:
			self.last_batch_request_list.remove( edges )

		if 1 > len( self.last_batch_request_list ):
			return True

		print( f"len == {len( self.last_batch_request_list )}" )
		# There are(is an) element(s) in self.last_batch_request_list
		return False

	def load_items_into_loader(self, loader = None, text = {}, url = "", now = ""):
		loader.add_value("url", url)
		loader.add_value("project", self.settings.get("BOT_NAME") )
		loader.add_value("spider", self.name )
		loader.add_value("server", socket.gethostname() )
		loader.add_value("date", now )

		loader.add_value( "content", str(text) )
		loader.add_value( "page_type", "json" )
		
		return loader

	def get_json_file_name(self, url_str = "", status_int = -4 ):
		now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		rectangle = ""
		url_obj = parse.urlparse(url_str)
		if hasattr( url_obj, "query" ):
			query_dict = parse.parse_qs( url_obj.query )
			if "rectangle" in query_dict.keys():
				rectangle = query_dict["rectangle"]
				if isinstance( rectangle, list ) and 0 < len( rectangle ):
					rectangle = rectangle[0]
				rectangle = rectangle.strip("'")
				rectangle = rectangle.replace(";", "___")
				rectangle = rectangle.replace(",", "_")
		if 1 > len( rectangle ):
			return ""
		return os.path.join( self.json_dir, f"{self.city_or_area_name}___{rectangle}___{status_int}___{now}.json" )

	def save_json(self, response=None, page_type = "json" ):
		"""
			during this tryout running, we still save the json response.body. But we will NOT in future.
		"""
		status = -4
		infocode = 0
		result_dict = {}
		if response is None or not hasattr(response, "body") or not hasattr( response, "url" ) or not hasattr( response, "meta"):
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, bad response object" )
			return (-1, infocode, f"wrong response object", result_dict)
		file_path = ""
		if "json" == page_type:
			json_dict = json.loads( response.body )
			status = json_dict["status"] if "status" in json_dict.keys() else "404"
			result_dict = json_dict["trafficinfo"] if "trafficinfo" in json_dict.keys() else {}
			infocode = json_dict["infocode"] if "infocode" in json_dict.keys() else ""
			status = int( status )
			infocode = int( infocode ) if isinstance( infocode, str ) and 0 < len( infocode ) else 0
			file_path = self.get_json_file_name( url_str = response.url, status_int = status )
		else:
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, wrong parameter page_type == {page_type} from {response.url}" )
			return (-2, infocode, f"page_type can ONLY be json", result_dict)
		
		return_msg = "written"
		if 0 < len( file_path ):
			try:
				with open( file_path, "wb" ) as f:
					f.write( response.body )
			except Exception as ex:
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, failed to write response.body from {response.url}" )
				return (status, infocode, f"failed to write json file", result_dict) # not -3
		return ( status, infocode, return_msg, result_dict )
