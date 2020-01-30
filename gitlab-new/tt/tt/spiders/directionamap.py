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
import socket
from urllib import parse

from scrapy.loader import ItemLoader
from scrapy.http import TextResponse

from tt.extensions.commonfunctions import CommonClass
from directionamap.items import DirectionamapItem

class FileFormatException(Exception):
	def __init__(self):
		Exception.__init__(self)

class DirectionamapSpider(scrapy.Spider):
	"""
		sys.exit code == 2 # missing CITY_LIST or missing input file(s)
		sys.exit code == 3 # classification file format error
		sys.exit code == 4 # already requested all xy points in city_list today
	"""
	name = "directionamap"
	
	root_path = ""
	log_dir = ""
	# debug = False
	# save_every_response = False
	crawled_dir = ""
	json_dir = ""
	output_folder_name = ""
	# output_file_format = "json"
	# base_uri = ""
	# run_purpose = None
	custom_settings = CommonClass.get_custom_settings_dict( spider=name )

	# crontab will start a new process in every 2 hours; therefore in 1 day, the crontab will start 12 times
	maximal_requests_of_one_crontab_process = 23
	interval_between_requests = 300
	request_counter = 0
	last_4_requests = {}

	urls = [
		"https://restapi.amap.com/v3/direction/driving?origin=113.268029,22.923338&destination=113.3025,23.38575&extensions=all&output=json&key=4ebb849f151dddb3e9aab7abe6e344e2",
		"https://restapi.amap.com/v3/direction/driving?origin=113.30508,23.38597&destination=113.268029,22.923338&extensions=all&output=json&key=470fdf698e3aab758d4cb026244f5194",
		"https://restapi.amap.com/v3/direction/driving?origin=113.268029,22.923338&destination=113.81424,22.62471&extensions=all&output=json&key=740f50c6fabd5801d0fad1cba62446d9",
		"https://restapi.amap.com/v3/direction/driving?origin=113.81276,22.62405&destination=113.268029,22.923338&extensions=all&output=json&key=4328d392605802de34406045b9701bb8",
	]
	# 0 == 碧桂园总部到白云机场；1 == 白云机场到碧桂园总部；2 == 总部到宝安机场；3 == 宝安机场到总部

	# https://restapi.amap.com/v3/direction/driving?origin=113.267982,22.92451&destination=113.307605,23.389929&extensions=all&output=json&key=4ebb849f151dddb3e9aab7abe6e344e2
	# https://restapi.amap.com/v3/direction/driving?origin=113.307605,23.389929&destination=113.267982,22.92451&extensions=all&output=json&key=4ebb849f151dddb3e9aab7abe6e344e2
	# 碧桂园总部
	# 113.268029,22.923338

	# 白云机场
	# 113.3025,23.38575:	T1航站楼国内出发
	# 113.30508,23.38597:	T1航站楼国内到达

	# 宝安机场
	# 113.81424,22.62471:	T3航站楼国内出发
	# 113.81276,22.62405:	T3航站楼国内到达

	# https://restapi.amap.com/v3/direction/driving?origin=113.267982,22.92451&destination=113.814829,22.633092&extensions=all&output=json&key=4ebb849f151dddb3e9aab7abe6e344e2
	# https://restapi.amap.com/v3/direction/driving?origin=113.814829,22.633092&destination=113.267982,22.92451&extensions=all&output=json&key=4ebb849f151dddb3e9aab7abe6e344e2
	
	# https://ditu.amap.com/dir?from%5Badcode%5D=440306&from%5Bname%5D=%E6%B7%B1%E5%9C%B3%E5%AE%9D%E5%AE%89%E5%9B%BD%E9%99%85%E6%9C%BA%E5%9C%BA&from%5Bid%5D=B02F37T239&from%5Bpoitype%5D=150104&from%5Blnglat%5D=113.81482900000003%2C22.633092&from%5Bmodxy%5D=113.815186%2C22.624847&to%5Bname%5D=%E7%A2%A7%E6%A1%82%E5%9B%AD%E6%80%BB%E9%83%A8&to%5Blnglat%5D=113.267982%2C22.92451&to%5Bid%5D=B0FFFVAF72&to%5Bpoitype%5D=120201&to%5Badcode%5D=440600&to%5Bmodxy%5D=113.269254%2C22.923768&type=car&policy=1
	# https://www.amap.com/dir?from%5Bname%5D=%E7%A2%A7%E6%A1%82%E5%9B%AD%E6%80%BB%E9%83%A8&from%5Blnglat%5D=113.267982%2C22.92451&from%5Bid%5D=B0FFFVAF72-from&from%5Bpoitype%5D=120201&from%5Badcode%5D=440600&from%5Bmodxy%5D=113.269254%2C22.923768&to%5Bid%5D=B0FFG40CGO&to%5Bname%5D=%E5%B9%BF%E5%B7%9E%E7%99%BD%E4%BA%91%E5%9B%BD%E9%99%85%E6%9C%BA%E5%9C%BAT1%E8%88%AA%E7%AB%99%E6%A5%BC(F3%E5%9B%BD%E5%86%85%E5%87%BA%E5%8F%915%E5%8F%B7%E9%97%A8)&to%5Blnglat%5D=113.302846%2C23.385712&to%5Bmodxy%5D=113.302846%2C23.385712&to%5Bpoitype%5D=150105&to%5Badcode%5D=440114&type=car&policy=1
	# https://www.amap.com/dir?from%5Bid%5D=B00140NZIQ&from%5Bname%5D=%E5%B9%BF%E5%B7%9E%E7%99%BD%E4%BA%91%E5%9B%BD%E9%99%85%E6%9C%BA%E5%9C%BA&from%5Blnglat%5D=113.307605%2C23.389929&from%5Bmodxy%5D=113.303722%2C23.385187&from%5Bpoitype%5D=150104&from%5Badcode%5D=440111&to%5Bname%5D=%E7%A2%A7%E6%A1%82%E5%9B%AD%E6%80%BB%E9%83%A8&to%5Blnglat%5D=113.267982%2C22.92451&to%5Bid%5D=B0FFFVAF72&to%5Bpoitype%5D=120201&to%5Badcode%5D=440600&to%5Bmodxy%5D=113.269254%2C22.923768&type=car&policy=1
	
	def init_self_attributes(self):
		self.root_path = self.settings.get( "PROJECT_PATH" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )
		# self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		# self.save_every_response = self.settings.get( name = "SAVE_EVERY_RESPONSE", default=False )
		self.crawled_dir = self.settings.get( name="CRAWLED_DIR", default = "" )
		self.json_dir = self.settings.get( name="SAVED_JSON", default="" )
		self.output_folder_name = self.settings.get( name="OUTPUT_FOLDER_NAME", default="" )
		# self.output_file_format = self.settings.get( name = "OUTPUT_FILE_FORMAT", default="json" )
		# self.base_uri = self.settings.get( name = "BASE_URI", default="" )
		self.run_purpose = self.settings.get( name = "RUN_PURPOSE", default=None )
		self.overwrite_today = self.settings.get( name = "OVERWRITE_TODAY", default="" )

		self.maximal_requests_of_one_crontab_process = self.settings.get( name="MAXIMAL_REQUESTS_OF_ONE_CRONTAB_PROCESS", default=23 )
		self.interval_between_requests = self.settings.get( name="INTERVAL_BETWEEN_REQUESTS", default=300 )

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
		if preset_route in [0, 1, 2, 3,]:
			return self.urls[ preset_route ]
		return ""
	
	def read_json_and_parse(self, response):
		file_list = os.listdir( self.json_dir )
		# route0___1___20190615_234522.json
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
							loader = ItemLoader( item = DirectionamapItem(), selector = json_selector )
							loader = self.load_items_into_loader( loader = loader, text = text_dict, url = url, now = now )
							yield loader.load_item()
					except Exception as ex:
						self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, error happened during loading ItemLoader. Exception = {ex}" )

	def extract_text_dict_from_response_body(self, body = "", preset_route = 101, now = "" ):
		text_dict = {}
		json_dict = json.loads( body )
		count = int(json_dict["count"]) # already 0 < count
		route_dict = json_dict["route"] if "route" in json_dict.keys() else {}
		paths = route_dict["paths"] if "paths" in route_dict.keys() else []
		duration = 0
		strategy = "速度最快"
		selected_path_steps = []
		found_fastest = False
		if 1 < len( paths ):
			for one_path in paths:
				temp_strategy = one_path["strategy"] if "strategy" in one_path.keys() else ""
				if -1 < temp_strategy.find("速度最快"):
					duration = int(one_path["duration"]) if "duration" in one_path.keys() else 0
					strategy = temp_strategy
					selected_path_steps = one_path["steps"] if "steps" in one_path.keys() else []
					found_fastest = True
					break
		if 1 == len( paths ) or ( not found_fastest and 1 < len(paths) ):
			duration = int(paths[0]["duration"]) if "duration" in paths[0].keys() else 0
			strategy = paths[0]["strategy"] if "strategy" in paths[0].keys() else ""
			selected_path_steps = paths[0]["steps"] if "steps" in paths[0].keys() else []

		text_dict = {
			"preset_route": preset_route,
			"strategy": strategy,
			"duration": duration,
			"count": count,
			"paths": len(paths),
			"now": now,
			"selected_path_steps": selected_path_steps,
		}

		return text_dict

	def parse_json(self, response):
		status, message = self.save_json( response = response, page_type = "json" )
		now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		preset_route = -1
		if 1 == status:
			try:
				meta_dict = response.meta
				preset_route = int(meta_dict["preset_route"])
				text_dict = self.extract_text_dict_from_response_body( body = response.body, preset_route = preset_route, now = now )
				loader = ItemLoader( item = DirectionamapItem(), response = response )
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
		loader.add_value("project", self.settings.get("BOT_NAME", default="") )
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
			count = int(json_dict["count"]) if "count" in json_dict.keys() else 0
			if 0 < count:
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
				return (status, f"failed to write json file")
		return ( status, return_msg )
