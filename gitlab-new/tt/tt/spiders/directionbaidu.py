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
from directionbaidu.items import DirectionbaiduItem

class FileFormatException(Exception):
	def __init__(self):
		Exception.__init__(self)

class DirectionamapSpider(scrapy.Spider):
	"""
		sys.exit code == 2 # missing CITY_LIST or missing input file(s)
		sys.exit code == 3 # classification file format error
		sys.exit code == 4 # already requested all xy points in city_list today
	"""
	name = "directionbaidu"
	
	root_path = ""
	log_dir = ""
	# debug = False
	# save_every_response = False
	crawled_dir = ""
	json_dir = ""
	output_folder_name = ""
	# output_file_format = "json"
	# base_uri = ""
	run_purpose = None
	overwrite_today = ""
	custom_settings = CommonClass.get_custom_settings_dict( spider=name )

	# crontab will start a new process in every 2 hours; therefore in 1 day, the crontab will start 12 times
	maximal_requests_of_one_crontab_process = 23
	interval_between_requests = 300
	request_counter = 0
	last_4_requests = {}

	urls = []

	def init_self_attributes(self):
		self.root_path = self.settings.get( "PROJECT_PATH" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )
		# self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		# self.save_every_response = self.settings.get( name = "SAVE_EVERY_RESPONSE", default=False )
		self.crawled_dir = self.settings.get( name="CRAWLED_DIR", default = "" )
		self.json_dir = self.settings.get( name="SAVED_JSON", default="" )
		self.output_folder_name = self.settings.get( name="OUTPUT_FOLDER_NAME", default="" )
		self.base_uri = self.settings.get( name = "BASE_URI", default="" )
		self.run_purpose = self.settings.get( name = "RUN_PURPOSE", default=None )
		self.overwrite_today = self.settings.get( name = "OVERWRITE_TODAY", default="" )

		self.maximal_requests_of_one_crontab_process = self.settings.get( name="MAXIMAL_REQUESTS_OF_ONE_CRONTAB_PROCESS", default=23 )
		self.interval_between_requests = self.settings.get( name="INTERVAL_BETWEEN_REQUESTS", default=300 )

		xy_points = {
			"country_garden": "22.9299453776,113.2749357238",
			"baiyun_airport_departure": "23.3932641265,113.3085855889", # T1航站楼国内出发
			"baiyun_airport_arrival": "23.3937931265,113.3068755889", # T1航站楼国内到达
			"baoan_airport_departure": "22.6303448273,113.8207143453", # T3航站楼国内出发
			"baoan_airport_arrival": "22.6296848273,113.8192343453", # T3航站楼国内到达
		}
		query_dict = {
			"origin": xy_points["country_garden"],
			"destination": xy_points["baiyun_airport_departure"],
			"coord_type": "bd09ll",
			"ret_coordtype": "bd09ll",
			"tactics": 7,
			"alternatives": 0,
			"output": "json",
			"ak": "iL3ZmAje32Q6WrXgaWcBSZP0RZG1hekL",
		}

		# 0 == 碧桂园总部到白云机场；1 == 白云机场到碧桂园总部；2 == 总部到宝安机场；3 == 宝安机场到总部
		query_list = []
		query_list.append(query_dict)

		temp_dict = copy.deepcopy( query_dict )
		temp_dict["origin"] = xy_points["baiyun_airport_arrival"]
		temp_dict["destination"] = xy_points["country_garden"]
		query_list.append(temp_dict)

		temp_dict = copy.deepcopy( query_dict )
		temp_dict["origin"] = xy_points["country_garden"]
		temp_dict["destination"] = xy_points["baoan_airport_departure"]
		query_list.append(temp_dict)

		temp_dict = copy.deepcopy( query_dict )
		temp_dict["origin"] = xy_points["baoan_airport_arrival"]
		temp_dict["destination"] = xy_points["country_garden"]
		query_list.append( temp_dict )

		for one_query_dict in query_list:
			self.urls.append( f"{self.base_uri}?{parse.urlencode(one_query_dict)}" )

		if 4 != len( self.urls ):
			self.logger.error( f"self.urls length shall be 4 ({self.urls})" )

	def check_dirs_and_files(self):
		if not os.path.isdir( self.crawled_dir ):
			os.makedirs( self.crawled_dir )
		if not os.path.isdir( self.json_dir ):
			os.makedirs( self.json_dir )

	def start_requests(self):
		self.init_self_attributes()
		self.check_dirs_and_files()

		if "READ_JSON_AND_WRITE_CSV" == self.run_purpose:
			one_url = "https://blog.csdn.net/qq_37193537/article/details/78987949"
			callback_func = self.read_json_and_parse
			yield scrapy.Request( url=one_url, callback=callback_func, dont_filter = True )
		else:
			timestamp_float = time.time()
			self.last_4_requests = {
				"request_time": timestamp_float,
				"requested_index": [0, 1, 2, 3,]
			}
			callback_func = self.parse_json
			for index, one_url in enumerate( self.urls ):
				meta_dict = {
					"preset_route": index, # 0 == 碧桂园总部到白云机场；1 == 白云机场到碧桂园总部；2 == 总部到宝安机场；3 == 宝安机场到总部
					"redo": 0,
				}
				self.logger.info( f"{index}: requesting {one_url} ")
				yield scrapy.Request( url=one_url, callback=callback_func, meta = meta_dict, dont_filter = True )

	def get_url_according_to_preset_route( self, preset_route = 101 ):
		# 由于有一个严重的bug直到20190619_2220才修补，导致在这之前的所有请求都是宝安机场到总部的(即preset_route == 3)
		baoan2headquarter = "http://api.map.baidu.com/direction/v2/driving?origin=22.6296848273%2C113.8192343453&destination=22.9299453776%2C113.2749357238&coord_type=bd09ll&ret_coordtype=bd09ll&tactics=7&alternatives=0&output=json&ak=iL3ZmAje32Q6WrXgaWcBSZP0RZG1hekL"
		if 0 < len( self.overwrite_today ) and "READ_JSON_AND_WRITE_CSV" == self.run_purpose:
			time_array = time.strptime( self.overwrite_today, "%Y%m%d")
			timestamp_overwrite_today = float( time.mktime(time_array) )
			time_array = time.strptime( "20190619_222000", "%Y%m%d_%H%M%S")
			timestamp_bug_fixed = float( time.mktime(time_array) )
			if timestamp_overwrite_today < timestamp_bug_fixed:
				return baoan2headquarter
		if 3 == preset_route:
			return baoan2headquarter
		elif 2 == preset_route:
			return "http://api.map.baidu.com/direction/v2/driving?origin=22.9299453776%2C113.2749357238&destination=22.6303448273%2C113.8207143453&coord_type=bd09ll&ret_coordtype=bd09ll&tactics=7&alternatives=0&output=json&ak=iL3ZmAje32Q6WrXgaWcBSZP0RZG1hekL"
		elif 1 == preset_route:
			return "http://api.map.baidu.com/direction/v2/driving?origin=23.3937931265%2C113.3068755889&destination=22.9299453776%2C113.2749357238&coord_type=bd09ll&ret_coordtype=bd09ll&tactics=7&alternatives=0&output=json&ak=iL3ZmAje32Q6WrXgaWcBSZP0RZG1hekL"
		elif 0 == preset_route:
			return "http://api.map.baidu.com/direction/v2/driving?origin=22.9299453776%2C113.2749357238&destination=23.3932641265%2C113.3085855889&coord_type=bd09ll&ret_coordtype=bd09ll&tactics=7&alternatives=0&output=json&ak=iL3ZmAje32Q6WrXgaWcBSZP0RZG1hekL"
		return ""
	
	def read_json_and_parse(self, response):
		file_list = os.listdir( self.json_dir )
		# route0___0___20190615_234522.json
		for one_file in file_list:
			temp_list = one_file.split("___")
			preset_route = 0
			now = ""
			if 2 < len( temp_list ):
				preset_route = temp_list[0]
				preset_route = preset_route.lstrip("route")
				preset_route = CommonClass.find_digits_from_str( string = preset_route, return_all = False)
				preset_route = int( preset_route )
				now = temp_list[2]
				now = now.rstrip(".json")

				url = self.get_url_according_to_preset_route( preset_route = preset_route )
				json_file_path = os.path.join( self.json_dir, one_file )
				if os.path.isfile(json_file_path):
					try:
						doc = None
						with open( json_file_path, "rb") as f:
							doc = f.read().decode("utf-8", "ignore")
						if doc is None:
							self.logger.error( f"Error: cannot read html file {json_file_path}.")
							continue
						text_dict = self.extract_text_dict_from_response_body( body = doc, preset_route = preset_route, now = now )
						if 0 < len( text_dict ):
							json_selector = Selector( text=doc, type=None )
							loader = ItemLoader( item = DirectionbaiduItem(), selector = json_selector )
							loader = self.load_items_into_loader( loader = loader, text = text_dict, url = url, now = now )
							yield loader.load_item()
					except Exception as ex:
						self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, error happened during loading ItemLoader. Exception = {ex}" )

	def extract_text_dict_from_response_body(self, body = "", preset_route = 101, now = "" ):
		text_dict = {}
		json_dict = json.loads( body )
		result_dict = json_dict["result"] if "result" in json_dict.keys() else {}
		total = int(result_dict["total"]) if "total" in result_dict.keys() else 0
		routes_list = result_dict["routes"] if "routes" in result_dict.keys() else []
		selected_route_dict = {}
		if 1 < len(routes_list):
			for one_route_dict in routes_list:
				tag = one_route_dict["tag"] if "tag" in one_route_dict.keys() else ""
				if -1 < tag.find( "推荐路线" ):
					selected_route_dict = one_route_dict
					break
		elif 1 == len(routes_list):
			selected_route_dict = routes_list[0]

		# if no 推荐路线, just select the first route_dict
		if 1 < len(routes_list):
			selected_route_dict = routes_list[0]

		if 0 < len( selected_route_dict ):
			tag = selected_route_dict["tag"] if "tag" in selected_route_dict.keys() else ""
			distance = selected_route_dict["distance"] if "distance" in selected_route_dict.keys() else 0
			duration = selected_route_dict["duration"] if "duration" in selected_route_dict.keys() else 0
			selected_path_steps = selected_route_dict["steps"] if "steps" in selected_route_dict.keys() else []

			text_dict = {
				"preset_route": preset_route,
				"strategy": tag,
				"duration": duration,
				"distance": distance,
				"count": total,
				"paths": len(routes_list),
				"now": now,
				"selected_path_steps": selected_path_steps,
			}
		return text_dict

	def parse_json(self, response):
		status, message = self.save_json( response = response, page_type = "json" )
		now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		preset_route = -1
		if 0 == status:
			try:
				meta_dict = response.meta
				preset_route = int(meta_dict["preset_route"])
				text_dict = self.extract_text_dict_from_response_body( body = response.body, preset_route = preset_route, now = now )
				if 0 < len( text_dict ):
					loader = ItemLoader( item = DirectionbaiduItem(), response = response )
					loader = self.load_items_into_loader( loader = loader, text = text_dict, url = response.url, now = now )
					yield loader.load_item()
			except Exception as ex:
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, error happened during loading ItemLoader. Exception = {ex}" )
		if -1 == preset_route:
			if hasattr( response, "meta" ):
				meta_dict = response.meta
				if "preset_route" in meta_dict.keys():
					preset_route = int( meta_dict["preset_route"] )
		if -1 < preset_route:
			received_all_4_requests_bool = self.check_this_preset_route(preset_route = preset_route)

			if not received_all_4_requests_bool and "redo" in response.meta.keys():
				delayed_index_list = self.get_delayed_response_more_than_1_minute()
				if 0 < len( delayed_index_list ):
					request_result_bool = self.redo_requests( redo = response.meta["redo"] )

			# get data again after 5 minutes
			if self.request_counter < self.maximal_requests_of_one_crontab_process and received_all_4_requests_bool:
				while( self.check_time_interval() ):
					time.sleep(10)
				
				self.request_counter += 1
				now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
				self.logger.info( f" requesting amap at {now} ( {self.request_counter} of { self.maximal_requests_of_one_crontab_process } )")
				self.last_4_requests = {
					"request_time": time.time(),
					"requested_index": [0, 1, 2, 3,]
				}
				callback_func = self.parse_json
				for index, one_url in enumerate( self.urls ):
					meta_dict = {
						"preset_route": index,
						"redo": 0,
					}
					self.logger.info( f"{index}: requesting {one_url} ")
					yield scrapy.Request( url=one_url, callback=callback_func, meta = meta_dict, dont_filter = True )

	def check_time_interval( self ):
		if "request_time" not in self.last_4_requests.keys() or not isinstance( self.last_4_requests["request_time"], float ):
			return False
		if time.time() - self.last_4_requests["request_time"] > float(self.interval_between_requests):
			return False
		return True

	def redo_requests(self, redo = -1 ):
		urls = []
		index_list = []
		if 1 > len( self.last_4_requests["requested_index"] ) or 0 > redo:
			return False
		for one_index in self.last_4_requests["requested_index"]:
			urls.append( self.urls[one_index] )
			index_list.append( one_index )
		now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		for index, one_url in enumerate( urls ):
			meta_dict = {
				"preset_route": index_list[index],
				"redo": redo + 1,
			}
			self.logger.info( f"[{now}] redo {index_list[index]}: requesting {one_url} ")
			yield scrapy.Request( url=one_url, callback=self.parse_json, meta = meta_dict, dont_filter = True )

	def get_delayed_response_more_than_1_minute( self ):
		if "requested_index" not in self.last_4_requests.keys() or not isinstance( self.last_4_requests["requested_index"], list ):
			return []
		if "request_time" not in self.last_4_requests.keys() or not isinstance( self.last_4_requests["request_time"], float ):
			return []
		if time.time() - self.last_4_requests["request_time"] > 60.0:
			return self.last_4_requests["requested_index"]
		return []

	def check_this_preset_route(self, preset_route = -1):
		if preset_route not in [0, 1, 2, 3, ]:
			return True
		if "request_time" not in self.last_4_requests.keys() or not isinstance( self.last_4_requests["request_time"], float ):
			return True
		if "requested_index" not in self.last_4_requests.keys() or not isinstance( self.last_4_requests["requested_index"], list ):
			return True

		# 4 minutes have passed, just return True
		if time.time() - self.last_4_requests["request_time"] > 240.0:
			return True

		# remove current preset_route
		if preset_route in self.last_4_requests["requested_index"]:
			self.last_4_requests["requested_index"].remove( preset_route )
		if 1 > len( self.last_4_requests["requested_index"] ):
			return True

		# There are(is a) element(s) in self.last_4_requests["requested_index"]
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

	def save_json(self, response=None, page_type = "json" ):
		status = -4
		if response is None or not hasattr(response, "body") or not hasattr( response, "url" ) or not hasattr( response, "meta"):
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, bad response object" )
			return (-1, f"wrong response object")
		meta_dict = response.meta
		preset_route = meta_dict["preset_route"] if "preset_route" in meta_dict.keys() else ""
		file_path = ""
		if "json" == page_type:
			json_dict = json.loads( response.body )
			status = json_dict["status"] if "status" in json_dict.keys() else "404"
			result_dict = json_dict["result"] if "result" in json_dict.keys() else {}
			routes_list = result_dict["routes"] if "routes" in result_dict.keys() else []
			if isinstance( routes_list, list ) and 0 < len( routes_list ):
				now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
				file_path = os.path.join( self.json_dir, f"route{preset_route}___{status}___{now}.json" )
				status = int( status )
		else:
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, wrong parameter page_type == {page_type} from {response.url}" )
			return (-2, f"page_type can ONLY be json")
		
		return_msg = "0 count"
		if 0 < len( file_path ):
			try:
				with open( file_path, 'wb' ) as f:
					f.write( response.body )
			except Exception as ex:
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, failed to write response.body from {response.url}" )
				return (status, f"failed to write json file") # not -3
		return ( status, return_msg )
