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
from poibaidu.items import PoibaiduItem

class FileFormatException(Exception):
	def __init__(self):
		Exception.__init__(self)

class PoibaiduSpider(scrapy.Spider):
	"""
		sys.exit code == 1 # missing input folder
		sys.exit code == 2 # missing CITY_LIST or missing input file(s)
		sys.exit code == 3 # classification file format error
		sys.exit code == 4 # already requested all xy points in city_list today
		sys.exit code == 5 # missing Baidu ak
		sys.exit code == 6 # Method make_request_uris of Class PoibaiduSpider, query_type can ONLY be 3
		sys.exit code == 7 # Run out of all Baidu ak today!
	"""
	name = "poibaidu"
	
	root_path = ""
	log_dir = ""
	baidu_ak_list = []
	debug = False
	save_every_response = False
	crawled_dir = ""
	json_dir = ""
	input_folder_name = ""
	output_folder_name = ""
	classification_filename = ""
	maximal_request_times = []
	output_file_format = "json"
	base_uri = ""
	query_type = 3
	query_type3edge = 0
	lng_delta = 0
	lat_delta = 0
	baidu_status_code = {}
	run_purpose = None
	city_list = []
	input_dir = ""
	bout = 0
	category_level = 1
	custom_settings = CommonClass.get_custom_settings_dict( spider=name )

	classification_dict = {}
	classification_dict_english_mapper = {}
	second_part_of_xy_filename = "2km_with_zero.txt"
	ak_pointer = 0
	center_dict = {}
	request_scope = 2 # 检索结果详细程度。取值为1 或空，则返回基本信息；取值为2，返回检索POI详细信息
	page_size = 20 # 百度API说最大值是每一次请求返回20条记录：http://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-placeapi

	# scrapy housekeeping keys:
	housekeeping_key_list = [ "download_slot", "download_latency", "depth", "query", ]

	bad_ak_status = [ 4, 5, 210, 211, 302, ]
		
	def init_self_attributes(self):
		self.root_path = self.settings.get( "PROJECT_PATH" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )
		self.baidu_ak_list = self.settings.get( name = "BAIDU_AK", default=[] )
		if 1 > len( self.baidu_ak_list ):
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, missing Baidu ak" )
			sys.exit(5)

		self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		self.save_every_response = self.settings.get( name = "SAVE_EVERY_RESPONSE", default=False )
		self.crawled_dir = self.settings.get( name="CRAWLED_DIR", default = "" )
		self.json_dir = self.settings.get( name="SAVED_JSON", default="" )
		self.input_folder_name = self.settings.get( name="INPUT_FOLDER_NAME", default="" )
		self.output_folder_name = self.settings.get( name="OUTPUT_FOLDER_NAME", default="" )
		self.classification_filename = self.settings.get( name="QUERY_CLASSIFICATION_FILENAME", default="" )
		self.maximal_request_times = self.settings.get( name = "MAXIMAL_REQUEST_TIMES", default=[] )
		self.output_file_format = self.settings.get( name = "OUTPUT_FILE_FORMAT", default="json" )
		self.base_uri = self.settings.get( name = "BASE_URI", default="" )
		self.query_type = self.settings.get( name = "QUERY_TYPE", default=3 )
		self.query_type3edge = self.settings.get( name = "QUERY_TYPE3EDGE", default=1.1 )
		# https://zhidao.baidu.com/question/138957118823573885.html
		# 北纬30度，应该是0.010402707553*edge
		# 北纬45度，应该是0.0127406627241*edge
		# 北纬60度，应该是0.01801801801802*edge
		self.lng_delta = 0.01167 * self.query_type3edge
		self.lat_delta = 0.009009009 * self.query_type3edge # 每一纬度是111公里
		self.baidu_status_code = self.settings.get( name = "BAIDU_STATUS_CODE", default={} )
		self.run_purpose = self.settings.get( name = "RUN_PURPOSE", default=None )
		self.city_list = self.settings.get( name = "CITY_LIST", default=[] )
		self.input_dir = os.path.join( self.root_path, self.name, self.input_folder_name )
		self.bout = self.settings.get( name = "RUN_PURPOSE_BOUT", default=1 )

		self.category_level = self.settings.get( name = "NEED_LEVELS", default=1 )

		self.classification_dict_english_mapper = self.settings.get( name = "DATABASE_ENGLISH_CATEGORY_TABLE", default={} )

	def check_dirs_and_files(self):
		if not os.path.isdir( self.crawled_dir ):
			os.makedirs( self.crawled_dir )
		if not os.path.isdir( self.json_dir ):
			os.makedirs( self.json_dir )
		
		# check all files and dirs
		if not os.path.isdir( self.input_dir ):
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, input folder ({self.input_dir}) and input files are needed." )
			sys.exit(1)
		
		temp_list = []
		missed_input_file = []
		for one_city in self.city_list:
			input_file_path = os.path.join( self.input_dir, f"{one_city}{self.second_part_of_xy_filename}" )
			if os.path.isfile( input_file_path ):
				temp_list.append( one_city )
			else:
				missed_input_file.append( one_city )
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, missing {input_file_path}" )
		if 0 < len(missed_input_file):
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, missing input files of {missed_input_file}" )
			sys.exit(2)
			# self.city_list = temp_list
		if 1 > len( self.city_list ):
			# errorMsg = f"Missing input files of {missed_input_file}" if 0 < len(missed_input_file) else f"please indicate which cities you want to request POIs"
			errorMsg = f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, please indicate which cities you want to request POIs"
			self.logger.error( errorMsg )
			sys.exit(2)

	def read_xy_file(self, city = ""):
		"""
		return a list [] that including this city's xy points
		"""
		center = []
		temp_list = []
		if 1 > len( city ):
			return center
		today = datetime.datetime.now().strftime("%Y%m%d")
		try:
			input_filename = f"{city}{self.second_part_of_xy_filename}"
			with open( os.path.join( self.input_dir, input_filename ), 'r', encoding='utf-8') as f:
				for item in f.readlines()[1:]:
					center.append(tuple(item.strip().split(",")[-5:])) # lng, lat, ok0, max_value, max_timestamp
		except Exception as ex:
			center = []
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, cannot read xy_list file ({input_filename}) or requested xy points file ({input_filename}). Exception = {ex}" )
		return center

	def parse_uri_query_to_dict(self, url = "", only_these_keys = [], map_query_english = True ):
		result_dict = {}
		query_part_list = url.split("?")
		if 2 == len( query_part_list ):
			result_dict = parse.parse_qs( query_part_list[1] )
		for index, key in enumerate( result_dict ):
			if 1 == len( result_dict[key] ):
				result_dict[key] = result_dict[key][0]
			else:
				self.logger.warning( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, length of {len(result_dict[key])} is more than 1" )
		if 0 < len( only_these_keys ):
			temp_dict = {}
			for index, key in enumerate( result_dict ):
				if key in only_these_keys:
					temp_dict[key] = result_dict[key]
			result_dict = temp_dict

		if "bounds" in result_dict.keys():
			result_dict["bounds"] = result_dict["bounds"].replace(",", "_")
		if map_query_english and "query" in result_dict.keys():
			if result_dict["query"] in self.classification_dict_english_mapper.keys():
				result_dict["query"] = self.classification_dict_english_mapper[ result_dict["query"] ]
			else:
				result_dict["query"] = f"unknown_english_name{random.randint(10000,99999)}"
		return result_dict

	def return_next_ak( self ):
		self.ak_pointer += 1
		if self.ak_pointer >= len( self.baidu_ak_list ): # do not use ==
			self.ak_pointer = 0
		return self.baidu_ak_list[self.ak_pointer]

	def make_request_uris(self, query_type = 3, exclude_requested_today = True ):
		"""
		As of 20190529, ONLY 3 == query_type is coded
		1 == query_type: "http://api.map.baidu.com/place/v2/search?query=ATM机&tag=银行&region=北京&output=json&ak=您的ak" # requesting pois in one city
		2 == query_type: "http://api.map.baidu.com/place/v2/search?query=银行&location=39.915,116.404&radius=2000&output=xml&ak=您的密钥" # requesting pois in one circle area
		3 == query_type: "http://api.map.baidu.com/place/v2/search?query=银行&bounds=39.915,116.404,39.975,116.414&output=json&ak={您的密钥}" # requesting pois in one rectangle area
		4 == query_type: "http://api.map.baidu.com/place/v2/detail?uid=435d7aea036e54355abbbcc8&output=json&scope=2&ak=您的密钥" # requesting pois at one location with detailed address
		"""
		base_uri = self.base_uri
		if 4 == query_type:
			base_uri = self.base_uri.replace("/search", "/detail")
		if 3 != query_type:
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, argumnet query_type can ONLY be 3; 1/2/4 are under developing" )
			sys.exit(6)

		today = datetime.datetime.now().strftime("%Y%m%d")
		urls = {}
		all_categories = []
		if 1 == self.category_level:
			all_categories = self.classification_dict.keys()
		elif 2 == self.category_level:
			for index, level1key in enumerate( self.classification_dict ):
				all_categories += self.classification_dict[level1key]
		elif 3 == self.category_level:
			all_categories = list(self.classification_dict.keys())
			for index, level1key in enumerate( self.classification_dict ):
				all_categories += self.classification_dict[level1key]
		for index, city in enumerate(self.center_dict):
			# read this city's log file to exclude today's requested points
			requested = []
			finished_xy_filename = f"{city}_finished_xy_query_points_{today}.log"
			finished_file_path = os.path.join( self.log_dir, finished_xy_filename )
			if exclude_requested_today and os.path.isfile( finished_file_path ):
				with open( finished_file_path, "r", encoding="utf-8") as log_file:
					for item in log_file.readlines():
						value = item.strip().split(",")
						if 3 == len(value):
							requested.append( f"{value[0]}___{value[1]}___{value[2]}" )
			
			excluded = []
			for category in all_categories:
				city_category_dict = {}
				for item in self.center_dict[city]:
					lng, lat, ok0, max_value, max_timestamp = item
					requested_key = f"{lng}___{lat}___{category}"
					if exclude_requested_today and 0 < len(requested):
						if requested_key in requested:
							excluded.append(requested_key)
							continue
					lng, lat = float(lng), float(lat)
					lng_min = float( "%.3f" % (lng - 0.5 * self.lng_delta) )
					lng_max = float( "%.3f" % (lng + 0.5 * self.lng_delta) )
					lat_min = float( "%.3f" % (lat - 0.5 * self.lat_delta) )
					lat_max = float( "%.3f" % (lat + 0.5 * self.lat_delta) )
					bounds = f"{lat_min},{lng_min},{lat_max},{lng_max}"
					city_category_dict[requested_key] = f"{base_uri}?query={category}&page_size={self.page_size}&page_num=0&scope={self.request_scope}&bounds={bounds}&output={self.output_file_format}&ak={self.return_next_ak()}"
				if 0 < len( city_category_dict ):
					urls[ f"{city}___{category}" ] = city_category_dict
			if 0 < len(excluded):
				self.logger.info( f"{len(excluded)} requests have been excluded in City {city}: ({excluded})" )
		return urls

	def make_point_request_from_500_by_500( self, url_fragment_list = [] ):
		url = url_fragment_list[-1]
		bounds = ""
		xy_list = []
		new_center = {}
		if 0 < len( url ):
			result_dict = parse.parse_qs( url )
			if 0 < len( result_dict ) and "bounds" in result_dict.keys():
				bounds = result_dict["bounds"][0]
		if 0 < len( bounds ):
			xy_list = bounds.split(",")
		if 4 == len( xy_list ):
			# bounds=23.091,113.306,23.097,113.313
			y_min = float(xy_list[0])
			x_min = float(xy_list[1])
			y_max = float(xy_list[2])
			x_max = float(xy_list[3])
			delta_x = int(1000 * ( x_max - x_min ))
			delta_y = int(1000 * ( y_max - y_min ))
			if 0 < delta_x and 0 < delta_y:
				for i in range( delta_x ):
					for j in range( delta_y ):
						key_x = "%.6f" % (x_min + i / 1000)
						key_y = "%.5f" % (y_min + j / 1000)
						x = "%.3f" % (x_min + i / 1000)
						y = "%.3f" % (y_min + j / 1000)
						x_plus_1 = "%.3f" % (x_min + (i + 1) / 1000)
						y_plus_1 = "%.3f" % (y_min + (j + 1) / 1000)
						new_center[ f"{key_x}___{key_y}" ] = f"{y},{x},{y_plus_1},{x_plus_1}"
		return new_center

	def make_16_request_from_2km_by_2km( self, url_fragment_list = [] ):
		new_center = {}
		lng, lat = float(url_fragment_list[0]), float(url_fragment_list[1])
		if 0 < lng and 0 < lat:
			center_xy = [lng, lat,]
			new_center = self.get_center_xys_from_single_xy( center_xy, half_edge_seperator = 2, query_type3edge = 1.1 )
		return new_center
		
	def get_center_xys_from_single_xy(self, center_xy = [], half_edge_seperator = 2, query_type3edge = 1.1 ):
		new_center = {}
		if not isinstance( half_edge_seperator, int ):
			return new_center
		lng, lat = float(center_xy[0]), float(center_xy[1])
		old_half_edge = float( "%.3f" % (query_type3edge / 1.1) )
		xy_point_list = []
		new_span = old_half_edge / half_edge_seperator
		lng_delta = 0.01167 * new_span
		lat_delta = 0.009009009 * new_span
		x_minimal = "%.6f" % (lng - (half_edge_seperator - 0.5) * lng_delta)
		y_minimal = "%.5f" % (lat - (half_edge_seperator - 0.5) * lat_delta)
		for i in range( half_edge_seperator * 2 ):
			for j in range( half_edge_seperator * 2 ):
				x = "%.6f" % (lng + i * lng_delta)
				y = "%.5f" % (lat + j * lat_delta)
				key = f"{x}___{y}"
				xy_point_list.append( key )
		for one in xy_point_list:
			temp_list = one.split("___")
			if 2 == len( temp_list ):
				bound_string = self.get_small_bounds(center_xy = temp_list, query_type3edge = new_span * 1.2 ) # for smaller rectangle, we use 1.2
				if 0 < len( bound_string ):
					new_center[ one ] = bound_string
		return new_center

	def get_small_bounds(self, center_xy = [], query_type3edge = 0.55 ):
		lng_delta = 0.01167 * query_type3edge
		lat_delta = 0.009009009 * query_type3edge
		lng, lat = float(center_xy[0]), float(center_xy[1])
		lng_min = float( "%.3f" % (lng - 0.5 * lng_delta) )
		lng_max = float( "%.3f" % (lng + 0.5 * lng_delta) )
		lat_min = float( "%.3f" % (lat - 0.5 * lat_delta) )
		lat_max = float( "%.3f" % (lat + 0.5 * lat_delta) )
		if 0 < lng_min and 0 < lng_max and 0 < lat_min and 0 < lat_max:
			return f"{lat_min},{lng_min},{lat_max},{lng_max}"
		else:
			return ""

	def do_makeup_requests(self, query_type = 3, bout = 1, single_line = "" ):
		all_city_dict = {}
		if bout not in [1, 2,] or 3 != query_type:
			return all_city_dict
		
		base_uri = self.base_uri
		if 4 == query_type:
			base_uri = self.base_uri.replace("/search", "/detail")
		if 0 == len( single_line ):
			today = datetime.datetime.now().strftime("%Y%m%d")
			empty_file_dir = os.path.join( self.root_path, self.name, self.output_folder_name, f"{today}waiting4next" )
			file_list = os.listdir( empty_file_dir )
			all_lines = []
			for one_file in file_list:
				try:
					this_file_path = os.path.join( empty_file_dir, one_file )
					with open( this_file_path, 'r', encoding='utf-8') as f:
						for item in f.readlines():
							all_lines.append(item)
				except Exception as ex:
					all_lines = []
					self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, cannot read xy_list file ({this_file_path}). Exception = {ex}" )
		else:
			all_lines = [ single_line ]
		new_center = {}
		

		for item in all_lines:
			url_fragment_list = item.strip().split("___")
			if 1 == bout:
				new_center = self.make_16_request_from_2km_by_2km( url_fragment_list )
			elif 2 == bout:
				new_center = self.make_point_request_from_500_by_500( url_fragment_list )
			category = url_fragment_list[2]
			city = url_fragment_list[3]
			city_category_key = f"{city}___{category}"
			for index, key in enumerate(new_center):
				temp_list = key.split("___")
				if 2 == len( temp_list ):
					requested_key = f"{temp_list[0]}___{temp_list[1]}___{category}"
					bounds = new_center[ key ]
					temp_dict = {}
					if city_category_key in all_city_dict.keys():
						temp_dict = all_city_dict[city_category_key]
					temp_dict[requested_key] = f"{base_uri}?query={category}&page_size={self.page_size}&page_num=0&scope={self.request_scope}&bounds={bounds}&output={self.output_file_format}&ak={self.return_next_ak()}"
					all_city_dict[city_category_key] = temp_dict
		return all_city_dict

	def start_requests(self):
		self.init_self_attributes()
		self.check_dirs_and_files()
		self.read_classification_file()
		self.center_dict = {}
		for city in self.city_list:
			center_list = self.read_xy_file( city = city )
			if 0 < len( center_list ):
				self.center_dict[city] = center_list
		if 1 > len( self.center_dict ):
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, you already requested all xy points in {self.city_list} today." )
			sys.exit(4)

		if "REDO_OVER400_POIS" == self.run_purpose:
			url_dict = self.do_makeup_requests( query_type = 3, bout = self.bout, single_line = "" )
		else:
			url_dict = self.make_request_uris( query_type = 3, exclude_requested_today = True )
		callback_func = self.parse_json
		if self.debug:
			callback_func = self.do_nothing_for_debug

		meta_dict = {}
		for index, key in enumerate(url_dict):
			temp_list = key.split("___")
			if 2 == len( temp_list ):
				meta_dict = {
					"city": temp_list[0],
					"category": temp_list[1],
					"page_num": 0,
				}
				for inner_index, center_xy in enumerate( url_dict[key] ):
					one_url = url_dict[key][center_xy]
					temp_list = center_xy.split("___")
					if 3 == len( temp_list ):
						meta_dict["center_x"] = temp_list[0]
						meta_dict["center_y"] = temp_list[1]
						if "REDO_OVER400_POIS" == self.run_purpose:
							self.logger.info( f"requesting {one_url}; meta = {meta_dict}" )
						else:
							self.logger.info( f"requesting {one_url}" )
						yield scrapy.Request( url=one_url, callback=callback_func, meta = meta_dict, dont_filter = True )
					else:
						self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {center_xy} error in url_dict[key] ({len(url_dict[key])})" )
			else:
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {key} error in url_dict ({len(url_dict)})" )
				continue

	def do_nothing_for_debug(self, response):
		pass

	def parse_json(self, response):
		status, message = self.save_json( response = response, page_type = "json" )
		callback_func = self.parse_json
		url = response.url
		today = datetime.datetime.now().strftime("%Y%m%d")
		if status in [-1, -2, -3,]:
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, wrong parameter(s) have passed to self.save_json!" )
		elif 404 == status:
			meta_dict = self.request_counter_and_action(response = response)
			if 0 < meta_dict["request_counter"]:
				yield scrapy.Request( url = response.url, callback = callback_func, meta = meta_dict, dont_filter = True )
		elif status in [ 2, 3, ]:
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, failed to request {response.url} using wrong parameters or verification error(s)" )
		elif status in self.bad_ak_status:
			self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, failed to request {response.url}; run out of Baidu Ak quota or wrong settings; status code {status}" )
			temp_list = message.split("___")
			if 4 == len( temp_list ):
				bad_ak = temp_list[3]
				if 0 < len( bad_ak ) and bad_ak in self.baidu_ak_list:
					self.baidu_ak_list.remove( bad_ak )
				if 1 > len( self.baidu_ak_list ):
					self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, run out of all Baidu ak today!" )
					sys.exit(7)
				else:
					yield scrapy.Request( url = response.url, callback = callback_func, meta = response.meta_dict, dont_filter = True )
			else:
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, self.save_json did NOT pass the bad ak back!" )
		elif 0 == status:
			temp_list = message.split("___")
			if 3 == len( temp_list ):
				page_num = int(temp_list[1])
				total = int(temp_list[2])
				will_divide_request = False
				if 400 <= total:
					meta_dict = {}
					if hasattr(response, "meta"):
						meta_dict = response.meta
					needed_keys = ["city", "center_x", "center_y",]
					city = meta_dict["city"] if "city" in meta_dict.keys() else ""
					center_x = meta_dict["center_x"] if "center_x" in meta_dict.keys() else ""
					center_y = meta_dict["center_y"] if "center_y" in meta_dict.keys() else ""
					query = meta_dict["category"] if "category" in meta_dict.keys() else ""
					content = f"{center_x}___{center_y}___{query}___{city}___{page_num}___{total}___{url}"

					# begin to request 16 times for 1 == bout or 0.001 step for 2 == bout
					bout = int(meta_dict["bout"]) if "bout" in meta_dict.keys() else 1
					if 3 > bout:
						url_dict = self.do_makeup_requests( query_type = 3, bout = bout, single_line = content )
						for index, key in enumerate(url_dict):
							temp_list = key.split("___")
							if 2 == len( temp_list ):
								meta_dict = {
									"city": temp_list[0],
									"category": temp_list[1],
									"page_num": 0,
									"bout": bout + 1,
								}
								for inner_index, center_xy in enumerate( url_dict[key] ):
									one_url = url_dict[key][center_xy]
									temp_list = center_xy.split("___")
									if 3 == len( temp_list ):
										meta_dict["center_x"] = temp_list[0]
										meta_dict["center_y"] = temp_list[1]
										self.logger.info( f"requesting {one_url}; meta = {meta_dict}" )
										yield scrapy.Request( url=one_url, callback=self.parse_json, meta = meta_dict, dont_filter = True )
									else:
										self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {center_xy} error in url_dict[key] ({len(url_dict[key])})" )
							else:
								self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {key} error in url_dict ({len(url_dict)})" )
								continue
						will_divide_request = True
					else:
						xy_over400_filename = f"{city}_over400_xy_{today}.log"
						self.write_log( content = content, logfilename = xy_over400_filename, content_only = True)
						will_divide_request = False
						# directly save this json file even it contains more than 400 POIs
				if not will_divide_request:
					json_dict = json.loads( response.body )
					result_list = json_dict["results"] if "results" in json_dict.keys() else []
					this_page_pois_list = []
					for one_poi in result_list:
						this_poi_dict = self.process_one_baidu_poi_json_dict( json_dict = one_poi )
						this_page_pois_list.append( this_poi_dict )

					housekeeping_dict = {}
					meta_dict = {}
					if hasattr(response, "meta"):
						meta_dict = response.meta
					for one_key in self.housekeeping_key_list:
						housekeeping_dict[one_key] = meta_dict[one_key] if one_key in meta_dict.keys() else ""
					housekeeping_dict["query"] = meta_dict["category"] if "category" in meta_dict.keys() else ""

					# yield to pipeline
					try:
						for one_poi in this_page_pois_list:
							loader = ItemLoader( item = PoibaiduItem(), response = response )
							loader = self.load_items_into_loader( loader = loader, one_poi_dict = one_poi, housekeeping_dict= housekeeping_dict, url = url )
							yield loader.load_item()
					except Exception as ex:
						self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, error happened during loading ItemLoader. Exception = {ex}" )

					last_page = math.ceil( total / self.page_size ) - 1
					if page_num < last_page and hasattr(response, "meta"):
						meta_dict["page_num"] = page_num + 1
						url = url.replace(f"page_num={page_num}", f"page_num={page_num+1}")
						yield scrapy.Request( url=url, callback=callback_func, meta = meta_dict, dont_filter = True )
					elif page_num < last_page:
						self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, missing response.meta while requesting {url} (last_page == {last_page})" )
					elif page_num >= last_page:
						# this one shall be else:, but we just add one more condition
						# write separate log before yielding to pipeline
						center_x = meta_dict["center_x"] if "center_x" in meta_dict.keys() else ""
						center_y = meta_dict["center_y"] if "center_y" in meta_dict.keys() else ""
						query = housekeeping_dict["query"]
						if 0 < len( meta_dict["city"] ) and 0 < len( center_x ) and 0 < len( center_y ) :
							city = meta_dict["city"]
							finished_xy_filename = f"{city}_finished_xy_query_points_{today}.log"
							self.write_log( content = f"{center_x},{center_y},{query}", logfilename = finished_xy_filename, content_only = True)
							# to have smaller I/O, we do NOT inlcude page_num and total_page here. Baidu API Server seems to be stronger than QQ
			else:
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, self.save_json did NOT pass correct message ({message})!" )

	def load_items_into_loader(self, loader = None, one_poi_dict = {}, housekeeping_dict = {}, url = ""):
		# record housekeeping fields
		for index, key in enumerate(housekeeping_dict):
			loader.add_value(key, housekeeping_dict[key])
		loader.add_value("url", url)
		loader.add_value("project", self.settings.get("BOT_NAME") )
		loader.add_value("spider", self.name )
		loader.add_value("server", socket.gethostname() )
		loader.add_value("date", datetime.datetime.now().strftime("%Y%m%d_%H%M%S") )

		# record all fields for database table(s)
		loader.add_value( "content", str(one_poi_dict) )
		loader.add_value( "page_type", "json" )
		
		return loader

	def print_attributes(self):
		for one in dir(self):
			if not callable( getattr(self, one) ) and -1 == one.find("__"):
				self.logger.info( f"{one} ==> {getattr(self, one)}" )

	def read_classification_file(self):
		classification_dict = {}
		classification_file_path = os.path.join( self.input_dir, self.classification_filename )
		try:
			with open( classification_file_path, 'r', encoding='utf-8') as f:
				for item in f.readlines():
					temp_list = item.strip().split(":")
					if 2 == len( temp_list ):
						value_list = temp_list[1].split("、") if -1 < temp_list[1].find( "、" ) else [temp_list[1]]
						classification_dict[ temp_list[0] ] = value_list
					else:
						raise FileFormatException
		except FileFormatException as ex:
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {item} cannot be splitted into 2 by a colon. Wrong format in File {classification_file_path}. Exception = {ex}" )
			sys.exit( 3 )
		except Exception as ex:
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, cannot read classification file ({classification_file_path}). Exception = {ex}" )
			sys.exit( 3 )
		self.classification_dict = classification_dict

	def extract_response_meta_to_dict(self, response = None):
		city = ""
		category = ""
		page_num = -1
		if hasattr(response, "meta") and "city" in response.meta.keys():
			city = response.meta["city"]
		if hasattr(response, "meta") and "category" in response.meta.keys():
			category = response.meta["category"]
		if hasattr(response, "meta") and "page_num" in response.meta.keys():
			page_num = int(response.meta["page_num"])
		return (city, category, page_num)

	def save_json(self, response=None, page_type = "json" ):
		if response is None or not hasattr(response, "body") or not hasattr( response, "url" ):
			return (-1, f"wrong response format")
		city = ""
		category = ""
		page_num = -1
		status = 404
		total = "0"
		bad_baidu_ak = False
		uri_query_dict = {}
		if "json" == page_type:
			json_dict = json.loads( response.body )
			status = json_dict["status"] if "status" in json_dict.keys() else "404"
			total = json_dict["total"] if "total" in json_dict.keys() else "0"
			only_these_keys = ["page_num", "query", "bounds", ]
			if int(status) in self.bad_ak_status:
				only_these_keys.append("ak")
				bad_baidu_ak = True
			uri_query_dict = self.parse_uri_query_to_dict( url = response.url, only_these_keys = only_these_keys, map_query_english = True )
			city, category, page_num = self.extract_response_meta_to_dict( response = response )
			page_num = uri_query_dict["page_num"]
			category = uri_query_dict["query"]
			bounds = uri_query_dict["bounds"]
			file_path = os.path.join( self.json_dir, f"{city}___{category}___{bounds}___{page_num}___{total}___{status}.json" )
			status = int( status )
		else:
			return (-2, f"page_type can ONLY be json")
		
		try:
			with open( file_path, 'wb' ) as f:
				f.write( response.body )
		except Exception as ex:
			self.logger.warning( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, failed to write response.body from {response.url}" )
			return (-3, f"failed to write json file")
		else:
			return_msg = f"# {page_num} of {total} pages is requested___{page_num}___{total}"
			if bad_baidu_ak:
				bad_ak = uri_query_dict["ak"] if "ak" in uri_query_dict.keys() else ""
				return_msg = f"# {page_num} of {total} pages is requested___{page_num}___{total}___{bad_ak}"
			return ( status, return_msg )

	def request_counter_and_action(self, response = None):
		return_dict = {}
		if hasattr( response, "meta" ):
			return_dict = response.meta
		request_counter = 0
		request_pointer = 0
		if hasattr( response, "meta" ) and "request_pointer" in response.meta.keys():
			request_pointer = int( response.meta["request_pointer"] )
			del return_dict["request_pointer"]
		if hasattr( response, "meta" ) and "request_counter" in response.meta.keys():
			request_counter = int(response.meta["request_counter"])
			del return_dict["request_counter"]

		if request_pointer < len( self.maximal_request_times ):
			self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, request_counter == {request_counter}; request_pointer == {request_pointer} for the last request from {response.url}" )
			if request_counter < self.maximal_request_times[request_pointer]:
				return_dict["request_counter"] = request_counter + 1
				return_dict["request_pointer"] = request_pointer
				return return_dict
			else:
				return_dict["request_counter"] = 1
				return_dict["request_pointer"] = request_pointer + 1
				return return_dict
		else:
			today = datetime.datetime.now().strftime("%Y%m%d")
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {self.maximal_request_times} requests have been sent but ONLY empty response.body received from {response.url}" )
			self.write_log( content = response.url, logfilename = f"missed_uris{today}.txt", content_only = True)
			return_dict["request_counter"] = -1
			return_dict["request_pointer"] = request_pointer
			return return_dict

	def process_one_baidu_poi_json_dict(self, json_dict = {}):
		return_dict = {}
		key_list = [
			"name", "address", "province", "city", "area", "telephone", "uid", "street_id", "detail",
		]

		for one_key in key_list:
			if one_key in json_dict.keys():
				return_dict[one_key] = json_dict[one_key]
				has_item = True
			else:
				return_dict[one_key] = ""

		# process "detail_info", "tag" and "type"
		if "detail_info" in json_dict.keys():
			return_dict["detail_info"] = str( json_dict["detail_info"] )
			if "type" in json_dict["detail_info"].keys():
				return_dict["type"] = json_dict["detail_info"]["type"]
			if "tag" in json_dict["detail_info"].keys():
				return_dict["tag"] = json_dict["detail_info"]["tag"]
		else:
			return_dict["detail_info"] = str( {} )
		if "type" not in return_dict.keys():
			return_dict["type"] = ""
		if "tag" not in return_dict.keys():
			return_dict["tag"] = ""

		# process "lat" and "lng"
		if "location" in json_dict.keys():
			location = json_dict["location"]
			if "lat" in location.keys() and "lng" in location.keys():
				return_dict["lat"] = location["lat"]
				return_dict["lng"] = location["lng"]
		if "lat" not in return_dict.keys():
			return_dict["lat"] = ""
		if "lng" not in return_dict.keys():
			return_dict["lng"] = ""

		return return_dict

	def write_log(self, content = None, logfilename = None, content_only = False):
		if content is not None and 0 < len( content ):
			today = datetime.datetime.now().strftime("%Y%m%d")
			if logfilename is None:
				logfilename = f"{self.name}{today}.log"
			try:
				with open( os.path.join( self.log_dir, logfilename ), 'a', encoding='utf-8') as f:
					if content_only:
						info = f"{str(content)}\n"
					else:
						info = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] {content}\n"
					f.write(info)
				return 1
			except Exception as ex:
				return 0
		return -1
