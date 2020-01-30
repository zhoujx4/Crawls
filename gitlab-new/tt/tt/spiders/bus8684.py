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
from bus8684.items import Bus8684Item

class FileFormatException(Exception):
	def __init__(self):
		Exception.__init__(self)

class Bus8684Spider(scrapy.Spider):
	"""
		sys.exit code == 1 # missing BUS8684_CITY_LIST
	"""
	name = "bus8684"
	
	root_path = ""
	log_dir = ""
	debug = False
	bus8684_city_list = []
	save_every_response = False
	crawled_dir = ""
	saved_html_dir = ""
	gaode_json_dir = ""
	output_folder_name = ""
	base_uri = ""
	run_purpose = None

	custom_settings = CommonClass.get_custom_settings_dict( spider=name )

	def init_self_attributes(self):
		self.root_path = self.settings.get( "PROJECT_PATH" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )
		self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		self.bus8684_city_list = self.settings.get( "BUS8684_CITY_LIST", default = [] )
		if 1 > len(self.bus8684_city_list):
			self.logger.error( f"missing BUS8684_CITY_LIST ({self.bus8684_city_list}) setting" )
			sys.exit(1)
		self.save_every_response = self.settings.get( name = "SAVE_EVERY_RESPONSE", default=False )
		self.crawled_dir = self.settings.get( name="CRAWLED_DIR", default = "" )
		self.saved_html_dir = self.settings.get( name = "SAVED_HTML", default="" )
		self.gaode_json_dir = self.settings.get( name = "SAVED_GAODE_JASON", default="" )
		self.output_folder_name = self.settings.get( name="OUTPUT_FOLDER_NAME", default="" )
		self.base_uri = self.settings.get( name = "BASE_URI", default="" )
		self.run_purpose = self.settings.get( name = "RUN_PURPOSE", default=None )

		self.maximal_requests_of_one_crontab_process = self.settings.get( name="MAXIMAL_REQUESTS_OF_ONE_CRONTAB_PROCESS", default=23 )
		self.interval_between_requests = self.settings.get( name="INTERVAL_BETWEEN_REQUESTS", default=300 )

	def check_dirs_and_files(self):
		if not os.path.isdir( self.crawled_dir ):
			os.makedirs( self.crawled_dir )
		if not os.path.isdir( self.saved_html_dir ):
			os.makedirs( self.saved_html_dir )
		if not os.path.isdir( self.gaode_json_dir ):
			os.makedirs( self.gaode_json_dir )

	def start_requests(self):
		"""
			0 == index_level and "index" == page_type: https://guangzhou.8684.cn/
			1 == index_level: https://guangzhou.8684.cn/list1 # list1 page displays links of Bus Route #1, #10, #175 and so on
			"detailed" == page_type: https://guangzhou.8684.cn/x_8234e473 # this one is Bus Route 10 detailed page
		"""
		self.init_self_attributes()
		self.check_dirs_and_files()

		if "PRODUCTION_RUN" == self.run_purpose:
			number_day_of_this_year = datetime.datetime.now().timetuple().tm_yday # type == int
			seperate_into_days = self.settings.get( "CRAWL_BATCHES", default = 3 )
			if seperate_into_days > len( self.bus8684_city_list ):
				seperate_into_days = len( self.bus8684_city_list )
			batch_count = math.ceil( len( self.bus8684_city_list ) / seperate_into_days )
			today_batch = number_day_of_this_year % seperate_into_days
			start_index = today_batch * batch_count - 1
			end_index = ( today_batch + 1 ) * batch_count
			urls = []
			for index, city in enumerate(self.bus8684_city_list):
				if (start_index < index) and (index < end_index):
					urls.append( f"https://{city}.{self.base_uri}" )
			
			meta_dict = {
				"page_type": "index",
				"index_level": 0,
			}
			for url in urls:
				yield scrapy.Request( url = url, callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
		elif "READ_HTML" == self.run_purpose:
			url = "http://quotes.toscrape.com/page/1/"
			yield scrapy.Request( url = url, callback = self.debug_one_method, meta = {}, dont_filter = True )

	def extract_links_from_list_page(self, response = None, city = "", index_level_int = 0, route_str = "" ):
		urls = []
		if index_level_int not in [0, 1,]:
			return urls
		if 0 == index_level_int:
			digit_href_list = response.xpath("//div[@class='bus_kt_r1']/a/@href").extract()
			letter_href_list = response.xpath("//div[@class='bus_kt_r2']/a/@href").extract()
			all_link_list = digit_href_list + letter_href_list
			for one_link in all_link_list:
				urls.append( f"https://{city}.{self.base_uri}{one_link}" )
				# https://guangzhou.8684.cn/list1
				# one_link == "/list1", "/listB"
			return urls

		# 1 == index_level_int
		route_href_list = response.xpath("//div[@id='con_site_1']/a/@href").extract()
		route_text_list = response.xpath("//div[@id='con_site_1']/a/text()").extract()
		if len( route_href_list ) != len( route_text_list ):
			error_msg = f"length of route_href_list ({len(route_href_list)}) != length of route_text_list ({len(route_text_list)})"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			route_text_list = []
		for index, one_link in enumerate(route_href_list):
			temp_dict = {
				"url": f"https://{city}.{self.base_uri}{one_link}",
				# https://guangzhou.8684.cn/x_face82cc
				# one_link == "/x_f2148667", "/x_a72d3ade"
				"route": route_text_list[ index ] if index < len( route_text_list ) else 0,
			}
			urls.append( temp_dict )
		return urls

	def parse_list_page(self, response = None):
		write_result_int, city, page_type, index_level, route_str = self.save_html( response = response )
		if -1 == write_result_int or "index" != page_type or index_level not in [0, 1,]:
			return False

		urls = self.extract_links_from_list_page( response = response, city = city, index_level_int = index_level, route_str = route_str )
		if 0 == index_level:
			meta_dict = {
				"page_type": "index",
				"index_level": 1,
			}
			for one_url in urls:
				yield scrapy.Request( url = one_url, callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
		else:
			meta_dict = {
				"page_type": "detailed",
				"index_level": -1,
			}
			for one_url_dict in urls:
				meta_dict["route"] = one_url_dict["route"] if "route" in one_url_dict.keys() else "unknown_route"
				one_url = one_url_dict["url"] if "url" in one_url_dict.keys() else ""
				if 0 < len( one_url ):
					yield scrapy.Request( url = one_url, callback = self.parse_detailed_page, meta = meta_dict, dont_filter = True )
				else:
					error_msg = f"wrong one_url_dict ({one_url_dict})"
					self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		
	def get_city_from_url(self, url = ""):
		city = ""
		result_obj = parse.urlparse(url)
		if -1 < result_obj.netloc.find( self.base_uri ):
			temp2_list = result_obj.netloc.split(".")
			if 3 == len( temp2_list ):
				city = temp2_list[0]
		return city

	def make_html_file_name( self, response = None, city = "", index_level = -1 ):
		"""
			https://guangzhou.8684.cn/
			https://guangzhou.8684.cn/list1, https://guangzhou.8684.cn/listH
			https://guangzhou.8684.cn/x_8234e473, https://guangzhou.8684.cn/x_1ed58fbc
			response already has url and meta attributes
		"""
		now = datetime.datetime.now()
		html_filename_str = now.strftime("%Y%m%d_%H%M%S")
		today = now.strftime("%Y%m%d")

		url = response.url
		meta_dict = response.meta

		result_obj = parse.urlparse(url)
		url_path_list = result_obj.path.split("/")
		while "" in url_path_list:
			url_path_list.remove("")

		detailed_page_bool = False
		route_str = ""
		if 0 == len( url_path_list ) and 0 == index_level:
			html_filename_str = f"{city}___index{index_level}___route_all___{today}.html"
		elif 1 == len( url_path_list ):
			if -1 < url_path_list[0].find( "list" ):
				route_str = url_path_list[0].lstrip( "list" )
				if 1 > len( route_str ):
					route_str = "unknown"
				html_filename_str = f"{city}___index{index_level}___route_{route_str}___{today}.html"
			elif -1 < url_path_list[0].find( "x_" ):
				detailed_page_bool = True
				route_str = str( meta_dict["route"] ) if "route" in meta_dict.keys() else "unknown"
				# has Chinese and Entrobus32 does not accept file name including Chinese
				route_id = url_path_list[0]
				html_filename_str = f"{city}___detailed___route_{route_id}___{today}.html"
		else:
			html_filename_str = f"{city}___unknown___route_unknown___{html_filename_str}.html"
		return (detailed_page_bool, route_str, html_filename_str)

	def save_html(self, response = None):
		"""
			returns -1: wrong response object
			-2: fail to write response.body
			1001: this is a detailed page
			101: more than 69 pages
			0 to 70: page number; 0:detailed page or fail to extract total page from list page
		"""
		if response is None or not hasattr( response, "meta" ) or not hasattr( response, "body" ) or not hasattr( response, "url" ):
			if hasattr( response, "url" ):
				error_msg = f"fail to save response.body after requesting {response.url}; response has no body or meta attribute(s)"
			else:
				error_msg = f"fail to save response.body response has no url attribute and may have no body and / or meta attribute(s)"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return (-1, "", "", -1, "")
		url = response.url
		meta_dict = response.meta
		page_type = "index"
		index_level = -1
		route_str = ""
		city = self.get_city_from_url( url = url )
		html_file_path = ""

		if "page_type" in meta_dict.keys():
			page_type = meta_dict["page_type"]

		if "index_level" in meta_dict.keys():
			index_level = meta_dict["index_level"]
			index_level = CommonClass.safely_convert_to_int( to_int_obj = index_level, spider_obj = self, convert_strategy = "match_all_digits" )
			if index_level is None:
				index_level = -1
		elif "index" == page_type:
			error_msg = f"index_level is NOT in meta_dict.keys(); and page has NOT been saved after requesting {url} "
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		
		if "index" == page_type and -1 < index_level:
			detailed_page_bool, route_str, html_filename_str = self.make_html_file_name( response = response, city = city, index_level = index_level )
			html_file_path = os.path.join( self.saved_html_dir, html_filename_str )
		elif "detailed" == page_type:
			detailed_page_bool, route_str, html_filename_str = self.make_html_file_name( response = response, city = city, index_level = index_level )
			html_file_path = os.path.join( self.saved_html_dir, html_filename_str )

		try:
			with open( html_file_path, "wb" ) as f:
				f.write( response.body )
		except Exception as ex:
			error_msg = f"fail to write response.body into {html_file_path} after requesting {url}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return (0, city, page_type, index_level, route_str)
		return (1, city, page_type, index_level, route_str)

	def parse_one_bus_route_fields(self, response = None, city_str = "", route_str = "" ):
		if response is None:
			return {}

		try:
			url = response.url
			url_obj = parse.urlparse(url)
			bus_route_id = url_obj.path.strip("/")
			bus_line_div = response.xpath("//div[@id='bus_line']")
			bus_line_information_div = bus_line_div.xpath("./div[@class='bus_line_information ']/div[@class='bus_i_content']")
			bus_route_title = bus_line_information_div.xpath("./div[@class='bus_i_t1']/h1/text()").extract_first(default="")
			bus_route_title = CommonClass.clean_string( string = bus_route_title, char_to_remove = [' ','　','\xa0', '&nbsp',])
			bus_route_district = bus_line_information_div.xpath("./div[@class='bus_i_t1']/a[@class='bus_i_t2']/text()").extract_first(default="")
			bus_route_info_list = bus_line_information_div.xpath("./p[@class='bus_i_t4']/text()").extract()
			bus_route_info_str = ""
			if 0 < len( bus_route_info_list ):
				bus_route_info_str = "___".join( bus_route_info_list )
			bus_operation_interval_str = bus_line_div.xpath("./div[@class='bus_label ']/p[@class='bus_label_t2']/text()").extract_first(default="")
			
			bus_direction_dict = {}
			all_way_div_list = bus_line_div.xpath("./div[@class='bus_line_top ']")
			for index, one_way_div in enumerate(all_way_div_list):
				one_way_name_text_list = one_way_div.xpath("./div/strong/text()").extract()
				one_way_name = "___".join( one_way_name_text_list) if 0 < len( one_way_name_text_list) else ""
				span_text_list = one_way_div.xpath("./span/text()").extract()
				one_way_stop_number = "___".join( span_text_list ) if 0 < len( span_text_list) else ""
				if 0 < len( one_way_stop_number ):
					one_way_stop_number = CommonClass.clean_string( string = one_way_stop_number, char_to_remove = [' ','　','\xa0',])
				temp_dict = {
					"one_way_name": one_way_name,
					"one_way_stop_number": one_way_stop_number,
				}
				bus_direction_dict[ index ] = temp_dict

			bus_route_stop_round_trip_list = bus_line_div.xpath("./div[@class='bus_line_site ']")
			for index, one_direction in enumerate(bus_route_stop_round_trip_list):
				stop_sequence_list = one_direction.xpath("./div[@class='bus_site_layer']/div/i/text()").extract()
				stop_name_list = one_direction.xpath("./div[@class='bus_site_layer']/div/a/text()").extract()
				if len( stop_name_list ) == len( stop_sequence_list ):
					temp_list = []
					for stop_name_index, stop_name in enumerate( stop_name_list ):
						temp_list.append( f"{stop_sequence_list[stop_name_index]}___{stop_name}" )
					if index in bus_direction_dict.keys():
						bus_direction_dict[ index ]["stops"] = temp_list
					else:
						bus_direction_dict[ index ] = {"stops": temp_list}
			
			text_dict = {
				"route_title": bus_route_title.strip(),
				"city": city_str,
				"route_name": route_str,
				"route_id": bus_route_id.strip(),
				"route_uri": url,
				"route_district": bus_route_district.strip(),
				"route_info": bus_route_info_str.strip(),
				"operation_interval": bus_operation_interval_str.strip(),
				"bus_directions": bus_direction_dict,
			}
			return text_dict
		except Exception as ex:
			error_msg = f"Error happened during parsing. Exception = {ex}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return {}

	def debug_one_method(self, response):
		file_name = "guangzhou___detailed___route_405路(2019年7月13日起调整)___20190622.html"
		file_name = "guangzhou___detailed___route_花6路___20190622.html"
		html_dir = os.path.join( self.root_path, self.name, self.output_folder_name, "20190622html" )
		file_path = os.path.join( html_dir, file_name )
		if os.path.isfile( file_path ):
			doc = None
			try:
				with open( file_path, "rb" ) as html_file:
					doc = html_file.read().decode( "utf-8", "ignore" )
			except Exception as ex:
				self.logger.error( f"Error: cannot read html file {file_path}. Exception = {ex}")
				return False
			
			if doc is None:
				self.logger.error( f"Error: cannot read html file {file_path}.")
				return False
			url = "https://guangzhou.8684.cn/x_f2148667"
			response_for_items = TextResponse( url = url, status = 200, body = bytes(doc, encoding="utf-8") )

			write_result_int, city, page_type, index_level, route_str = self.save_html( response = response_for_items )
			text_dict = self.parse_one_bus_route_fields( response = response_for_items, city_str = city, route_str = route_str )
			text_dict["city"] = "guangzhou"
			text_dict["route_name"] = "花6路"
			if 0 < len( text_dict ):
				try:
					loader = ItemLoader( item = Bus8684Item(), response = response_for_items )
					loader = self.load_items_into_loader( loader = loader, text = text_dict, url = url )
					yield loader.load_item()
				except Exception as ex:
					self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, fail to load item. Exception = {ex}" )

	def parse_detailed_page(self, response):
		write_result_int, city, page_type, index_level, route_str = self.save_html( response = response )
		text_dict = self.parse_one_bus_route_fields( response = response, city_str = city, route_str = route_str )
		# self.logger.debug( f"write_result_int, city, page_type, index_level, route_str = {(write_result_int, city, page_type, index_level, route_str)}" )
		if 0 < len( text_dict ):
			self.logger.info( f"After requesting {response.url}, good response is received.")
			try:
				loader = ItemLoader( item = Bus8684Item(), response = response )
				loader = self.load_items_into_loader( loader = loader, text = text_dict, url = response.url )
				yield loader.load_item()
			except Exception as ex:
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, fail to load item. Exception = {ex}" )


	def load_items_into_loader(self, loader = None, text = {}, url = ""):
		loader.add_value("url", url)
		loader.add_value("project", self.settings.get("BOT_NAME") )
		loader.add_value("spider", self.name )
		loader.add_value("server", socket.gethostname() )
		loader.add_value("date", datetime.datetime.now().strftime("%Y%m%d_%H%M%S") )

		loader.add_value( "content", str(text) )
		loader.add_value( "page_type", "detailed" )
		
		return loader
