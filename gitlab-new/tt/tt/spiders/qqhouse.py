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
from collections import Iterable

from scrapy.loader import ItemLoader
from scrapy.http import TextResponse

from tt.extensions.commonfunctions import CommonClass
from qqhouse.items import QqhouseItem

class QqhouseSpider(scrapy.Spider):
	"""
		sys.exit code == 1 # missing CITIES_FOR_CRAWLING
		sys.exit code == 2 # wrong or missing CITY_PAGE_DICT
		sys.exit code == 3 # wrong value(s) of CITY_PAGE_DICT
		On 20190527 Peter re-write this spider for fixing bugs
	"""
	name = "qqhouse"
	
	root_path = ""
	run_purpose = None
	missed_id_txt_filename = ""
	maximal_request_times = []
	debug = None
	city_page_dict = {}
	maximal_list_pages = 0
	city_list = []
	save_every_response = False
	crawled_dir = ""
	detail_html_dir = ""
	list_html_dir = ""
	output_folder_name = ""
	log_dir = ""
	custom_settings = CommonClass.get_custom_settings_dict( spider=name )

	date_list = []
		
	def init_self_attributes(self):
		self.root_path = self.settings.get( "PROJECT_PATH" )
		self.run_purpose = self.settings.get( name = "RUN_PURPOSE", default=None )
		self.missed_id_txt_filename = self.settings.get( name = "MISSED_ID_TXT", default="" )
		self.maximal_request_times = self.settings.get( name = "MAXIMAL_REQUEST_TIMES", default=[] )
		self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		self.city_page_dict = self.settings.get( name = "CITY_PAGE_DICT", default={} )
		self.maximal_list_pages = self.settings.get( name = "MAXIMAL_LIST_PAGES", default=0 )
		self.city_list = self.settings.get( name = "CITIES_FOR_CRAWLING", default=[] )
		self.save_every_response = self.settings.get( name = "SAVE_EVERY_RESPONSE", default=False )
		self.crawled_dir = self.settings.get( name="CRAWLED_DIR", default = "" )
		self.detail_html_dir = self.settings.get( name="SAVED_DETAIL_HTML", default="" )
		self.list_html_dir = self.settings.get( name="SAVED_LIST_HTML", default="" )
		self.output_folder_name = self.settings.get( name="OUTPUT_FOLDER_NAME", default="" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )

	def make_dirs(self):
		# even cache is used, we save all html files; here we make these 3 dirs if they do not exist
		if not os.path.isdir( self.crawled_dir ):
			os.makedirs( self.crawled_dir )
		if not os.path.isdir( self.detail_html_dir ):
			os.makedirs( self.detail_html_dir )
		if not os.path.isdir( self.list_html_dir ):
			os.makedirs( self.list_html_dir )

	def start_requests(self):
		self.init_self_attributes()
		self.make_dirs()

		urls = []
		callback_func = self.parse_list
		meta_dict = {"page_type": "list"}
		if 1 > len( self.city_list ):
			self.logger.error( f"self.city_list can NOT be empty." )
			sys.exit(1)
			
		for one_city in self.city_list:
			if one_city not in self.city_page_dict.keys():
				self.logger.error( f"{one_city} is NOT in {self.city_page_dict}" )
				sys.exit(2)
			if 1 > int( self.city_page_dict[ one_city ] ):
				self.logger.error( f"Wrong value of {self.city_page_dict[one_city]} (key == {one_city})" )
				sys.exit(3)
			if 0 != self.maximal_list_pages and self.maximal_list_pages < int( self.city_page_dict[ one_city ] ):
				self.city_page_dict[ one_city ] = self.maximal_list_pages

		for one_city in self.city_list:
			for i in range( int( self.city_page_dict[ one_city ] ) ): # list_page urls
				urls.append( f"https://db.house.qq.com/index.php?mod=search&act=newsearch&city={one_city}&showtype=1&page_no={i+1}" )

		if self.debug:
			self.logger.debug( urls )
			urls = [
				"http://quotes.toscrape.com/page/1/",
				"http://quotes.toscrape.com/page/2/",
			]
			callback_func = self.do_nothing_for_debug
		elif "REDO_MISSED_HOUSE_IDS" == self.run_purpose:
			# REDO_MISSED_HOUSE_IDS is a special debug, HTTPCACHE_ENABLED == False before running REDO_MISSED_HOUSE_IDS
			urls = []
			try:
				file_path = os.path.join( self.root_path, self.name, self.output_folder_name, self.missed_id_txt_filename )
				city = "gz"
				with open( file_path, "r" ) as f:
					for one_id in f.readlines():
						one_id = one_id.replace("\n", "")
						urls.append( one_id ) # f"https://db.house.qq.com/{city}_{one_id}/"
			except Exception as ex:
				self.logger.error( f"failed to read missed_id_txt_file from {file_path}. Exception = {ex}" )
				sys.exit(4)
			callback_func = self.parse_detailed
		elif "REDO_MISSED_PAGE_IDS" == self.run_purpose:
			# REDO_MISSED_PAGE_IDS is a special debug, HTTPCACHE_ENABLED == False before running REDO_MISSED_PAGE_IDS
			urls = []
			try:
				file_path = os.path.join( self.root_path, self.name, self.output_folder_name, self.missed_id_txt_filename )
				city = "gz"
				with open( file_path, "r" ) as f:
					for one_id in f.readlines():
						one_id = one_id.replace("\n", "")
						urls.append( f"https://db.house.qq.com/index.php?mod=search&act=newsearch&city={city}&showtype=1&page_no={one_id}" )
			except Exception as ex:
				self.logger.error( f"failed to read missed_id_txt_file from {file_path}. Exception = {ex}" )
				sys.exit(4)
			callback_func = self.parse_list
		elif "READ_CSV_TO_KAFKA" == self.run_purpose:
			temp_list = self.settings.get( name="DATES_TO_BE_READ", default=[] )
			for one in temp_list:
				if isinstance( one, Iterable) and 0 < len( one ):
					temp_list.append( one )
			if 0 < len( temp_list ):
				self.date_list = temp_list
			callback_func = self.read_csv_to_kafka
			urls = [ "http://quotes.toscrape.com/page/1/", ]

		if self.run_purpose in ["REDO_MISSED_HOUSE_IDS", "REDO_MISSED_PAGE_IDS", "READ_CSV_TO_KAFKA", ]:
			for url in urls:
				yield scrapy.Request( url=url, callback=callback_func, meta = meta_dict, dont_filter = True )
		else:
			for url in urls:
				yield scrapy.Request( url=url, callback=callback_func, meta = meta_dict )

	def read_csv_to_kafka(self, response):
		# do not go to pipeline and just read csv file and produce message to Kafka
		if 1 > len( self.date_list ):
			return False
		for one_date in self.date_list:
			folder_name = f"{one_date}crawled"
			crawled_dir = os.path.join( self.root_path, self.name, self.output_folder_name, f"{today}crawled" )
			csv_file_path = os.path.join( crawled_dir, f"qqhouse{one_date}.csv" )
			if os.path.isdir( crawled_dir ) and os.path.isfile( csv_file_path ):
				with open( csv_file_path, newline="" ) as csvfile:
					file_reader = csv.reader(csvfile) # , delimiter=' ', quotechar='|'
					for row in file_reader:
						temp_dict = eval(row)
						print( temp_dict )
						print( type( temp_dict ) )

	def do_nothing_for_debug(self, response):
		self.logger.info( f"inside Method do_nothing_for_debug of Class QqhouseSpider. url = {response.url}" )

	def load_items_into_loader(self, loader = None, text = {}, url = ""):
		loader.add_value( 'content', str(text) ) # , encoding="utf-8"
		loader.add_value( 'page_type', "detailed" )

		# record housekeeping fields
		loader.add_value('url', url)
		loader.add_value('project', self.settings.get('BOT_NAME') )
		loader.add_value('spider', self.name )
		loader.add_value('server', socket.gethostname() )
		loader.add_value('date', datetime.datetime.now().strftime("%Y%m%d_%H%M%S") )
		return loader

	def get_list_html_file_path( self, city = "", page_no = 0 ):
		if 1 > len( city ) or 1 > page_no:
			return ""
		return os.path.join( self.list_html_dir, f"{city}_list_{page_no}.html" )

	def find_more_house_ids(self, doc = ""):
		house_id_list = []
		counter = 0
		index = 0
		while True:
			index = doc.find("data-hid", index)
			if -1 == index:
				break
			sub_doc = doc[index+10:index+25]
			house_id_list.append( CommonClass.find_digits_from_str( sub_doc ) )
			index += 10
			counter += 1
		return house_id_list

	def extract_all_detailed_html_links(self, string = ""):
		house_id_list = []
		if 1 > len( string ):
			return house_id_list
		doc = string.decode('utf-8')
		end_string = '";var search_result_list_num ='
		end_pos = len( doc )
		if -1 < doc.find( end_string ):
			end_pos = doc.find( end_string )
		doc = doc[ len('var search_result = "			'):end_pos ]
		doc = '<!DOCTYPE html><html><head lang="zh-cn"><title>腾讯房产列表</title></head><body>' + f"{doc}</body></html>"
		response = Selector( text=doc, type="html" )
		house_id_list = response.xpath("//div/@data-hid").extract()
		if 10 > len( house_id_list ):
			house_id_list = self.find_more_house_ids( doc = doc )
		else:
			temp_list = []
			for one_id in house_id_list:
				temp_list.append( CommonClass.find_digits_from_str( one_id ) )
			house_id_list = temp_list
		
		return house_id_list

	def parse_list(self, response = None):
		url = response.url
		city = ""
		page_no = 1
		page_type = "list"
		if hasattr( response, "meta" ) and "page_type" in response.meta.keys():
			page_type = response.meta["page_type"]
		
		if "list" == page_type:
			if 10 > len( str( response.body ) ): # cannot use 1 > ...
				meta_dict = self.request_counter_and_action(response = response)
				if 0 < meta_dict["request_counter"]:
					yield scrapy.Request( url=url, callback=self.parse_list, meta = meta_dict, dont_filter = True )
			else:
				house_id_list = []
				query_part_list = url.split("?")
				if 2 == len( query_part_list ):
					result_dict = parse.parse_qs( query_part_list[1] )
					if "city" in result_dict.keys() and 0 < len( result_dict["city"] ):
						city = result_dict["city"][0]
					if "page_no" in result_dict.keys() and 0 < len(result_dict["page_no"]) and 1 < int( result_dict["page_no"][0] ):
						page_no = int( result_dict["page_no"][0] )
					if self.save_every_response:
						list_html_file_path = self.get_list_html_file_path( city, page_no )
						if 0 < len( list_html_file_path ):
							self.save_html( response = response, page_type = "list", city = city, page_no= str(page_no), house_id = "" )
					house_id_list = self.extract_all_detailed_html_links( response.body )
					# counter = 0
					for one_id in house_id_list:
						next_url = f"https://db.house.qq.com/{city}_{one_id}/"
						self.logger.info( f"crawling next url at {next_url}" )
						yield response.follow( next_url, self.parse_detailed )
		else:
			self.logger.error( f"page_type ({page_type}) is NOT \"list\" in parse_list Method. url = {url}" )

	def load_items_into_loader(self, loader = None, text = {}, url = ""):
		loader.add_value( 'content', str(text) ) # , encoding="utf-8"
		loader.add_value( 'page_type', "detailed" )

		# record housekeeping fields
		loader.add_value('url', url)
		loader.add_value('project', self.settings.get('BOT_NAME') )
		loader.add_value('spider', self.name )
		loader.add_value('server', socket.gethostname() )
		loader.add_value('date', datetime.datetime.now().strftime("%Y%m%d_%H%M%S") )
		return loader

	def save_html(self, response=None, page_type = "detailed", city = "", page_no="", house_id = "" ):
		if response is None or not hasattr(response, "body") or not hasattr( response, "url" ):
			return False
		doc = response.body
		if "detailed" == page_type:
			temp_str = str( house_id ).zfill(8)
			file_path = os.path.join( self.detail_html_dir, f"{city}_{temp_str}.html" )
		elif "list" == page_type:
			temp_str = str( page_no ).zfill(4)
			file_path = os.path.join( self.list_html_dir, f"{city}_list{temp_str}.txt" )
		else:
			return False
		try:
			with open( file_path, 'wb' ) as f:
				f.write( doc )
		except Exception as ex:
			self.logger.warning( f"failed to write response.body from {response.url}" )
			return False
		return True

	def request_counter_and_action(self, response = None):
		request_counter = 0
		request_pointer = 0
		if hasattr( response, "meta" ) and "request_pointer" in response.meta.keys():
			request_pointer = int( response.meta["request_pointer"] )
		if hasattr( response, "meta" ) and "request_counter" in response.meta.keys():
			request_counter = int(response.meta["request_counter"])
		if request_pointer < len( self.maximal_request_times ):
			self.logger.info( f"request_counter == {request_counter}; request_pointer == {request_pointer} for the last request from {response.url}" )
			if request_counter < self.maximal_request_times[request_pointer]:
				return {
					"request_counter": request_counter + 1,
					"request_pointer": request_pointer,
				}
			else:
				return {
					"request_counter": 1,
					"request_pointer": request_pointer + 1,
				}
		else:
			today = datetime.datetime.now().strftime("%Y%m%d")
			self.logger.error( f"{self.maximal_request_times} requests have been sent but ONLY empty response.body received from {response.url}" )
			self.write_log( content = response.url, logfilename = f"missed_uris{today}.txt", content_only = True)
			return {
				"request_counter": -1,
				"request_pointer": request_pointer,
			}

	def extract_detailed_elements( self, response = None, city = "", house_id = "" ):
		text = {}

		# parse fields previously required
		big_box = response.css("div.item.fl")
		real_estate_name = response.css("div.name.fl div.cf h2::text").extract_first(default="")
		real_estate_slogan = big_box.css("div.hd.cf h1.Pagetitle::text").extract_first(default="")
		price_label = big_box.css("div.hd.cf h2.fl.yh.cf em.itemHeader::text").extract_first(default="")
		price_span_list = big_box.css("div.hd.cf h2.fl.yh.cf span.price::text").extract()
		price_span_money = big_box.css("div.hd.cf h2.fl.yh.cf span.price strong::text").extract_first(default="")
		if 2 == len( price_span_list ):
			price_str = f"{price_span_list[0]}___price___{price_span_money}___price___{price_span_list[1]}"
		else:
			price_str = "___price___".join(price_span_list)
			price_str = f"{price_str}___price___{price_span_money}"
		detail_lis = big_box.css( "ul.itemContent.itemContent3.pr li" )
		items = []
		for one_li in detail_lis:
			em_element = one_li.css( "em.itemHeader" )
			if em_element is not None and 0 < len(em_element):
				item_value_list = one_li.css( "::text" ).extract()
				item_value = ""
				if 1 < len( item_value_list ):
					for index, value in enumerate(item_value_list):
						item_value_list[index] = value.strip()
					item_value += str("".join(item_value_list))
				elif 1 == len( item_value_list ):
					item_value = item_value_list[0].strip()
				if "" != item_value:
					item_value = CommonClass.replace_string( string = item_value, char_to_remove = ['\r', '\n', '\t', ' ',], new_char = "___break___" )
					items.append( item_value )
			else:
				continue
		item_string = ""
		if 0 < len(items):
			item_string = "___descr___".join(items)
		if "" != item_string or "" != real_estate_name or "" != price_label or "" != price_str:
			text["real_estate_name"] = real_estate_name
			text["real_estate_slogan"] = real_estate_slogan
			text["price_label"] = price_label
			text["price_str"] = price_str
			text["item_string"] = item_string
			text["city"] = city
			text["house_id"] = house_id

		# parse fields required on 20190528
		basic_info_box = response.css("div#xxIntr ul.hdl.ft")
		all_lis = basic_info_box.xpath("./li")
		item_list = []
		for one_li in all_lis:
			key = one_li.xpath("./span/text()").extract_first(default="")
			value = one_li.xpath("./p/text()").extract_first(default="")
			if 0 < len( key ) and 0 < len( value ):
				item_list.append( f"{key}___key2value___{value}" )
		if 0 < len( item_list ):
			text["basic_info"] = "___basic___".join( item_list )

		return text

	def parse_detailed(self, response = None):
		# response=response.replace(encoding="gb2312") # do NOT use this line
		url = response.url
		doc = response.body
		doc = doc.decode("gb2312", "ignore")
		if 1 > len( str( doc ) ):
			meta_dict = self.request_counter_and_action(response = response)
			if 0 < meta_dict["request_counter"]:
				yield scrapy.Request( url=url, callback=self.parse_detailed, meta = meta_dict, dont_filter = True )
		else:
			city = ""
			house_id = ""
			url_list = url.split( "qq.com" )
			if 2 == len( url_list ):
				temp_list = url_list[1].replace("/", "")
				temp_list = temp_list.split("_")
				if 2 == len( temp_list ):
					city = temp_list[0]
					house_id = temp_list[1]
			if 0 < len( city) and 0 < len( house_id ):
				self.save_html( response = response, page_type = "detailed", city = city, house_id = house_id )
			
			text = {}
			try:
				response2 = Selector(text=doc, type="html")
				text = self.extract_detailed_elements( response = response2, city = city, house_id = house_id  )
			except Exception as ex:
				self.logger.error( f"Error! Exception = {ex}; text = {text}" )
			else:
				if 0 < len( text ):
					try:
						loader = ItemLoader( item = QqhouseItem(), response = response )
						loader = self.load_items_into_loader( loader = loader, text = text, url = url )
						yield loader.load_item()
					except Exception as ex:
						self.logger.error( f"Error happened during loading ItemLoader in Method parse_detailed of Class QqhouseSpider. Exception = {ex}" )
	
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