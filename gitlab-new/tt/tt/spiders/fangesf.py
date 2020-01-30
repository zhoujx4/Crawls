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
import hashlib
from urllib import parse

from scrapy.loader import ItemLoader
from scrapy.http import TextResponse

from tt.extensions.commonfunctions import CommonClass
from tt.extensions.proxyagents import ProxyAgent
from fangesf.items import FangesfItem

class FangesfSpider(scrapy.Spider):
	"""
		在分布式scrapyd部署之前，为了起多个fangesf进程而采取的临时措施(fangesfp2是本套代码的一个拷贝)。
		sys.exit code == 1 # wrong or missing RUN_PURPOSE
		sys.exit code == 2 # wrong or missing CRAWLED_DIR, SAVED_DETAIL_HTML, or SAVED_GAODE_JASON
		sys.exit code == 3 # fail to get proxy's ip
		On 20190605 Peter writes this spider upon requests
	"""
	name = "fangesf"

	root_path = ""
	log_dir = ""
	resume_break_point_detailed_file_name = "crawled_detailed_html.log"
	resume_break_point_list_file_name = "crawled_list_html.log"
	crawled_list_url_list = []
	crawled_detailed_url_list = []
	debug = False
	city_list = []
	district_list = []
	city_name_for_districts = ""
	run_purpose = None
	save_every_response = False
	overwrite_today = ""
	crawled_dir = ""
	saved_html_dir = ""
	gaode_json_dir = ""
	csv_file_path = None
	bedrooms_links = ["g21", "g22", "g23", "g24", "g25", "g299", ]
	over100_filename = ""

	custom_settings = CommonClass.get_custom_settings_dict(spider=name)

	proxy_ip_dict = {}
	min_proxy_ip_life_time = 6
	max_proxy_ip_life_time = 180
	use_proxy = False
	proxy_agent = ""
		
	def init_self_attributes(self):
		self.root_path = self.settings.get( "PROJECT_PATH" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )
		self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		self.city_name_for_districts = self.settings.get( "CITY_NAME_FOR_DISTRICTS", default = "city" )
		self.district_list = self.settings.get( "DISTRICT_LIST", default = [] )
		if 1 > len(self.district_list) and "city" != self.city_name_for_districts:
			self.logger.error( f"missing DISTRICT_LIST ({self.district_list}) setting" )
			sys.exit(1)
		self.city_list = self.settings.get( "CITY_LIST", default = [] )
		if 1 > len(self.city_list) and "city" == self.city_name_for_districts:
			self.logger.error( f"missing CITY_LIST ({self.city_list}) setting" )
			sys.exit(1)
		self.run_purpose = self.settings.get( name = "RUN_PURPOSE", default=None )
		if self.run_purpose is None:
			self.logger.error( f"missing RUN_PURPOSE ({self.run_purpose}) setting" )
			sys.exit(2)
		self.save_every_response = self.settings.get( name = "SAVE_EVERY_RESPONSE", default = False )
		self.overwrite_today = self.settings.get( "OVERWRITE_TODAY", default = "" )
		if not hasattr(self, "overwrite_today") or 1 > len( self.overwrite_today ) or self.overwrite_today is None:
			self.overwrite_today = datetime.datetime.now().strftime("%Y%m%d")

		# set all paths
		self.crawled_dir = self.settings.get( name = "CRAWLED_DIR", default = "" )
		self.saved_html_dir = self.settings.get( name = "SAVED_HTML", default="" )
		self.gaode_json_dir = self.settings.get( name = "SAVED_GAODE_JASON", default="" )
		self.csv_file_path = os.path.join( self.crawled_dir, f"fang_esf{self.overwrite_today}.csv" )

		if 1 > len( self.crawled_dir ) or 1 > len( self.saved_html_dir ) or 1 > len( self.gaode_json_dir ):
			error_msg = f"missing CRAWLED_DIR ({self.crawled_dir}), SAVED_HTML ({self.saved_html_dir}), or SAVED_GAODE_JASON ({self.gaode_json_dir}) setting(s)"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			sys.exit(3)

		self.over100_filename = self.settings.get( name = "OVER100_LOG_FILENAME", default="" )

		self.min_proxy_ip_life_time = self.settings.get( name = "MIN_PROXY_LIFE_SPAN", default = 6 )
		self.max_proxy_ip_life_time = self.settings.get( name = "MAX_PROXY_LIFE_SPAN", default = 180 )
		self.use_proxy = self.settings.get( name="HTTPPROXY_ENABLED", default = False )
		self.proxy_agent = self.settings.get( name="PROXY_AGENT", default = "" )

	def make_dirs(self):
		# even cache is used, we save all html files; here we make these 3 dirs if they do not exist
		if not os.path.isdir( self.crawled_dir ):
			os.makedirs( self.crawled_dir )
		if not os.path.isdir( self.saved_html_dir ):
			os.makedirs( self.saved_html_dir )
		if not os.path.isdir( self.gaode_json_dir ):
			os.makedirs( self.gaode_json_dir )

	def proxy_ip_pool(self):
		"""
			迅联错误码10000		提取过快，请至少5秒提取一次
		"""
		if "DRAGONFLY" == self.proxy_agent:
			return CommonClass.get_proxies( proxy_dict = {} )
		now = time.time()
		need_new_proxy = False
		if self.proxy_ip_dict is None or 1 > len( self.proxy_ip_dict ):
			need_new_proxy = True
		elif "expire" not in self.proxy_ip_dict.keys():
			need_new_proxy = True
		elif now + 3 > self.proxy_ip_dict["expire"]:
			need_new_proxy = True
		if need_new_proxy:
			proxies_dict = ProxyAgent.get_xunlian_proxy_dict(headers = {}, params_for_proxy_ip={}, setup_xunlian_dict = {}, need_setup_xunlian = False, logger=self.logger )
			if 1 > len( proxies_dict ):
				return self.proxy_ip_dict # still return the old ip dict or {}
			proxies_dict["expire"] = now + random.randint( self.min_proxy_ip_life_time, self.max_proxy_ip_life_time ) # set ip life time
			self.proxy_ip_dict = proxies_dict
		return self.proxy_ip_dict

	def read_crawled_urls(self):
		resume_break_point_detailed_file_path = os.path.join( self.log_dir, self.resume_break_point_detailed_file_name )
		try:
			with open( resume_break_point_detailed_file_path, "r", encoding="utf-8" ) as log_file:
				self.crawled_detailed_url_list = log_file.readlines()
				while "" in self.crawled_detailed_url_list:
					self.crawled_detailed_url_list.remove("")
		except Exception as ex:
			error_msg = f"fail to read {resume_break_point_detailed_file_path}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )

		# for list pages, do not use this [] to exclude seen urls
		# resume_break_point_list_file_path = os.path.join( self.log_dir, self.resume_break_point_list_file_name )
		# try:
		# 	with open( resume_break_point_list_file_path, "r", encoding="utf-8" ) as log_file:
		# 		self.crawled_list_url_list = log_file.readlines()
		# 		while "" in self.crawled_list_url_list:
		# 			self.crawled_list_url_list.remove("")
		# except Exception as ex:
		# 	error_msg = f"fail to read {resume_break_point_list_file_path}"
		# 	self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )

	def start_requests(self):
		self.init_self_attributes()
		self.make_dirs()
		self.read_crawled_urls()

		if "READ_HTML" == self.run_purpose: # READ_HTML is one kind of debug
			url = 'http://quotes.toscrape.com/page/1/'
			yield scrapy.Request( url = url, callback = self.read_and_parse )
		elif "PRODUCTION_RUN" == self.run_purpose:
			if "city" == self.city_name_for_districts:
				city_list = self.city_list
			else:
				city_list = self.district_list
			number_day_of_this_year = datetime.datetime.now().timetuple().tm_yday # type == int
			seperate_into_days = self.settings.get( "CRAWL_BATCHES", default = 3 )
			if seperate_into_days > len( city_list ):
				seperate_into_days = len( city_list )
			batch_count = math.ceil( len( city_list ) / seperate_into_days )
			today_batch = number_day_of_this_year % seperate_into_days
			start_index = today_batch * batch_count - 1
			end_index = ( today_batch + 1 ) * batch_count
			urls = []
			for index, city in enumerate(city_list):
				if (start_index < index) and (index < end_index):
					url = f"https://{city}.esf.fang.com/" if "city" == self.city_name_for_districts else f"https://{self.city_name_for_districts}.esf.fang.com/house-{city}/"
					urls.append( url )
			
			meta_dict = {
				"page_type": "index",
				"total_pages": 0,
				"index_level": 0,
			}
			if "city" != self.city_name_for_districts:
				meta_dict["index_level"] = 1

			if self.use_proxy:
				proxies_dict = self.proxy_ip_pool()
				if 1 > len( proxies_dict):
					sys.exit(3)
				meta_dict["proxy"] = proxies_dict["http"]
			
			for url in urls:
				yield scrapy.Request( url = url, callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
		elif "GET_CHANNELS" == self.run_purpose: # GET_CHANNELS is one kind of debug
			urls = []
			city_list = self.settings.get( "CITY_LIST", default = [] )
			for index, city in enumerate(city_list):
				urls.append( f"https://{city}.esf.fang.com/" )
			if 0 < len( urls ):
				meta_dict = {
					"page_type": "index",
					"total_pages": 0,
					"index_level": 0,
				}
				yield scrapy.Request( url = urls[0], callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
		elif "CHECK_PROXY_IP" == self.run_purpose:
			now = int(time.time())
			token = f"Guangzhou{str(now)}"
			m = hashlib.md5()  
			m.update( token.encode(encoding = 'utf-8') )
			urls = [
				f"https://www.coursehelper.site/index/index/getHeaders?token={m.hexdigest()}",
			]
			
			if "DRAGONFLY" == self.proxy_agent:
				proxies_dict = CommonClass.get_proxies( proxy_dict = {} )
			else:
				proxies_dict = ProxyAgent.get_xunlian_proxy_dict(headers = {}, params_for_proxy_ip={}, setup_xunlian_dict = {}, need_setup_xunlian = False, logger=self.logger )
			if 0 < len( proxies_dict):
				meta_dict = {
					"proxy": proxies_dict["http"]
				}
				for url in urls:
					yield scrapy.Request( url=url, callback=self.do_nothing_for_debug, meta = meta_dict )
			else:
				self.logger.error( f"Error! No proxy ip returns. {proxies_dict}" )
		else:
			urls = [
				"http://quotes.toscrape.com/page/1/",
				"http://quotes.toscrape.com/page/2/",
			]
			for url in urls:
				yield scrapy.Request( url=url, callback=self.do_nothing_for_debug )

	def get_total_pages( self, response = None ):
		"""
			if ONE page already includes all records, there is still one element called "共1页"
			if ONE page includes 0 record, there is no element called "共x页"
		"""
		total_pages = 0
		if response is None:
			return total_pages
		all_ps = response.xpath("//div[@id='list_D10_15']/p")
		total_pages_p = ""
		for one_p in all_ps:
			total_pages_p = one_p.xpath("./text()").extract_first(default = "")
			if 0 < len( total_pages_p ) and -1 < total_pages_p.find("共"):
				break
		if -1 < total_pages_p.find("共"):
			search_obj = re.search( r"(\d)+", total_pages_p, re.M|re.I )
			if search_obj is not None:
				start = search_obj.span()[0]
				end = search_obj.span()[1]
				if 0 < len( total_pages_p[start:end] ):
					total_pages = int( total_pages_p[start:end] )
		else:
			error_msg = f"cannot find total page at uri {response.url}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		return total_pages

	def get_city_from_url(self, url = ""):
		city = ""
		result_obj = parse.urlparse(url)
		if -1 < result_obj.netloc.find("fang.com"):
			temp2_list = result_obj.netloc.split(".")
			if 4 == len( temp2_list ):
				city = temp2_list[0]
		return city

	def make_html_file_name( self, url = "", city = "" ):
		now = datetime.datetime.now()
		html_filename = "{}.html".format( now.strftime("%Y%m%d_%H%M%S") )
		today = now.strftime("%Y%m%d")

		result_obj = parse.urlparse(url)
		url_list = result_obj.path.split("/")
		while "" in url_list:
			url_list.remove("")

		detail_page = False
		last_part = url_list[ len(url_list) -1 ] if 0 < len( url_list ) else ""
		if -1 < last_part.find( ".htm" ):
			detail_page = True
			# /chushou/3_218307566.htm ==> https://sz.esf.fang.com/chushou/3_218307566.htm
			temp = last_part.split( "_" )
			apt_id = f"{last_part}"
			if 1 < len(temp):
				apt_id = f"{temp[1]}"
			html_filename = f"{city}_{apt_id}_{today}.html"
		elif -1 < result_obj.netloc.find("fang.com") and 1 > len( url_list ):
			# list page #1: https://sz.esf.fang.com/
			html_filename = f"{city}_index1_{today}.html"
		else:
			page, district_area, bedrooms = self.get_page_and_district_area( url_list = url_list )
			
			if 0 < len( district_area ):
				html_filename = f"{city}_{district_area}_index{page}_{today}.html"
			else:
				html_filename = f"{city}_index{page}_{today}.html"
		return (detail_page, html_filename)

	def get_page_and_district_area(self, url_list = []):
		"""
			list page #2 or more, or including channels like:
			https://sz.esf.fang.com/house-a013080/
			where a013080 stands for 深圳市龙华区
			or https://sz.esf.fang.com/house-a013080-b014334 or https://sz.esf.fang.com/house-a013080-b02094/i372/
			where b014334 stands for 深圳市龙华区大浪；house-a013080-b02094 stands for 观澜；
			house-a013080-b0350 stands for 龙华；house-a013080-b014333 stands for 民治
			https://sz.esf.fang.com/house-a087-b0342/g22/ where g22 stands for 二居室；
			g21(一居)，g23(三居)，g24(四居)，g25(五居)，g299(五居以上)
			# this option is a multiple choice but this crawl will ONLY use single choice
		"""
		page = "1"
		district_area = ""
		bedrooms = 0
		for index, key in enumerate(url_list):
			one_fragment = url_list[ index ]
			if -1 < one_fragment.find("i3") and -1 == one_fragment.find("house-"):
				page = one_fragment[2:]
			elif -1 < one_fragment.find("house-") and -1 == one_fragment.find("i3"):
				district_area = one_fragment.replace("house-", "")
				district_area = district_area.replace("-", "_")
				if index + 1 < len( url_list ):
					next_fragment = url_list[ index + 1 ]
					if -1 < next_fragment.find("g2"):
						last_part_of_fragment = next_fragment.replace("g2", "")
						if -1 < last_part_of_fragment.find("-i3"):
							temp_list = last_part_of_fragment.split( "-i3" )
							if 1 < len( temp_list ):
								bedrooms = int( temp_list[0] )
						else:
							bedrooms = int( last_part_of_fragment )
		return (page, district_area, bedrooms)

	def save_html(self, response = None, save100 = False):
		if response is None or not hasattr( response, "meta" ) or not hasattr( response, "body" ) or not hasattr( response, "url" ):
			if hasattr( response, "url" ):
				error_msg = f"fail to save response.body after requesting {response.url}; response has no body or meta attribute(s)"
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return -1
		url = response.url
		meta_dict = response.meta
		page_type = "index"
		total_pages = 0
		city = self.get_city_from_url( url = url )

		if "page_type" in meta_dict.keys():
			page_type = meta_dict["page_type"]
		
		if "index" == page_type:
			if "total_pages" in meta_dict.keys():
				total_pages = int(meta_dict["total_pages"])

			if 0 == total_pages:
				total_pages = self.get_total_pages( response = response )

			if 99 < total_pages and not save100:
				return 101
			# https://sz.esf.fang.com/house-a013080/
			detail_page, html_filename = self.make_html_file_name( url = url, city = city )
			html_file_path = os.path.join( self.saved_html_dir, html_filename )
			save_html_file = True
			
		elif "detailed" == page_type:
			apt_id = self.get_apt_id(url = url)
			today = datetime.datetime.now().strftime("%Y%m%d")
			html_filename = f"{city}___{apt_id}___{today}.html"
			html_file_path = os.path.join( self.saved_html_dir, html_filename )
			save_html_file = True
			total_pages = 1001
			# https://sz.esf.fang.com/chushou/3_218307566.htm
		
		try:
			with open( html_file_path, "wb" ) as f:
				f.write( response.body )
		except Exception as ex:
			error_msg = f"fail to write response.body into {html_file_path} after requesting {url}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return -2
		else:
			if 1 > total_pages:
				error_msg = f"response.body saved after requesting {response.url}; but fail to extract total page number from response.body"
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return total_pages # could be 100 when save100 = True

	def extract_link_list( self, response = None ):
		link_list = response.xpath('//div[@class="shop_list shop_list_4"]/dl[@class="clearfix"]/dd/h4[@class="clearfix"]/a/@href').extract()
		if 1 > len( link_list ):
			error_msg = f"Fail to extract links from {response.url}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		return link_list

	def divide_request_into_next_level( self, response = None ):
		if response is None or not hasattr( response, "meta" ) or not hasattr( response, "body" ) or not hasattr( response, "url" ):
			error_msg = f"meta = {hasattr( response, 'meta' )}; body = {hasattr( response, 'body' )}; url = {hasattr( response, 'url' )}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return -1
		url = response.url
		result_obj = parse.urlparse(url)
		url_list = result_obj.path.split("/")
		while "" in url_list:
			url_list.remove("")
		meta_dict = response.meta
		index_level = 0
		if "index_level" in meta_dict.keys():
			index_level = int( meta_dict["index_level"] )
		page, district_area, bedrooms = self.get_page_and_district_area( url_list = url_list )

		if 0 < bedrooms:
			# as of 20190605, we ONLY care level upto bedrooms
			page_status = self.save_html( response = response, save100 = True )
			self.write_log( content = f"{response.url}", logfilename = self.over100_filename, content_only = True)

		# district_area has higher priority than index_level
		if 0 < len( district_area ):
			temp_list = district_area.split("_")
			if index_level != len( temp_list ):
				error_msg = f"index_level {index_level} != {len( temp_list )} ({district_area})"
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
				index_level = len( temp_list )
		else:
			if 0 != index_level:
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {index_level} is not 0" )
				index_level = 0

		pointer, link_list = self.extract_this_level_screen_options( response = response, index_level = index_level, district_area = district_area, bedrooms = 0 )
		return ( pointer, link_list, index_level )

	def make_new_url(self, url = "", index_level = 0, fragment = "" ):
		result_obj = parse.urlparse(url)
		url_path_list = result_obj.path.split("/")
		while "" in url_path_list:
			url_path_list.remove("")
		
		has_bedroom = False
		for one_path in url_path_list:
			if 0 == one_path.find("i3"):
				return ""
				# https://sz.esf.fang.com/house-a013080-b02094/i372/
			if 0 == one_path.find( "g2" ):
				has_bedroom = True
		if 2 == index_level:
			if has_bedroom and 0 == fragment.find( "g2" ):
				return ""
				# ONLY one option is selected
			return_url = f"{result_obj.scheme}://{result_obj.netloc}/{result_obj.path}{fragment}"
			if 0 == result_obj.path.find('/'):
				return_url = f"{result_obj.scheme}://{result_obj.netloc}{result_obj.path}{fragment}"
			return return_url
			# returns the first url: https://sz.esf.fang.com/house-a090-b0352/g23/
			# but for page #2 and above, url shall be: https://sz.esf.fang.com/house-a090-b0352/g23-i37/
		return_url = f"{result_obj.scheme}://{result_obj.netloc}/{fragment}"
		if 0 == fragment.find('/'):
			return_url = f"{result_obj.scheme}://{result_obj.netloc}{fragment}"
		return return_url

	def extract_this_level_screen_options(self, response = None, index_level = 0, district_area = "", bedrooms = 0 ):
		"""
			currently ONLY 1 > pointer will be returned
		"""
		link_list = []
		if 1 > index_level:
			link_list = response.xpath('//div[@class="screen_al"]/ul/li[@class="clearfix screen_list"]/ul[@class="clearfix choose_screen floatl"]/li/a/@href').extract()
			# remove 地铁线路
			temp_list = []
			for one_link in link_list:
				if -1 == one_link.find("house1-"):
					temp_list.append(one_link)
			link_list = temp_list
		elif 1 == index_level:
			link_list = response.xpath('//div[@class="screen_al"]/ul/li[@class="area_sq"]/ul[@class="clearfix"]/li/a/@href').extract()
		elif 2 == index_level:
			if 0 < bedrooms:
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {bedrooms} is not 0; as of 20190605, we ONLY have 3 levels to divide requests" )
				return (-1, [])	# this for future ONLY
			return (0, self.bedrooms_links)
		else:
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {index_level} over 2; as of 20190605, we ONLY have 3 levels to divide requests" )
			return (-1, [])
		temp_list = []
		for one_link in link_list:
			temp_string = one_link.replace("/", "")
			temp_string = temp_string.replace("house-", "")
			temp_list.append( temp_string.replace("-", "_") )
		pointer = 0 # currently ONLY 1 > pointer will be returned
		return (pointer, link_list)

	def load_items_into_loader(self, loader = None, text = {}, url = ""):
		loader.add_value( "content", str(text) ) # , encoding="utf-8"
		loader.add_value( "page_type", "detailed" )

		# record housekeeping fields
		loader.add_value( "url", url )
		loader.add_value( "project", self.settings.get('BOT_NAME') )
		loader.add_value( "spider", self.name )
		loader.add_value( "server", socket.gethostname() )
		loader.add_value( "date", datetime.datetime.now().strftime("%Y%m%d_%H%M%S") )
		return loader

	def parse_detailed_response_field(self, response = None, city = "", apt_id = ""):
		text = {}
		if response is None:
			return text
		if "READ_HTML" == self.run_purpose and not isinstance( response, Selector ):
			return text
		title = response.xpath("//div[@id='lpname']/h1/text()").extract_first(default="")
		if 1 > len( title ):
			title = response.xpath( "//div[@class='tab-cont clearfix']/div[@class='title rel']/h1[@class='title floatl']/text()" ).extract_first(default="")

		title_right_box = response.xpath("//div[@class='tab-cont-right']")
		price_div = title_right_box.xpath( "./div[@class='tr-line clearfix zf_new_title']/div[@class='trl-item_top']/div[@class='rel floatl']/preceding-sibling::div" )
		price_list = price_div.xpath( "string(.)" ).extract()
		price = "___".join( price_list )
		
		# extract features
		feature_div = title_right_box.xpath( "./div[@class='tr-line clearfix']/div[contains(@class,'trl-item1')]" )
		feature_dict = {}
		for one_item in feature_div:
			key = one_item.xpath( "./div[@class='font14']/text()" ).extract_first(default="")
			value = one_item.xpath( "./div[@class='tt']/text()" ).extract_first(default="")
			if 0 < len( key ):
				feature_dict[ key ] = CommonClass.clean_string( string = value, char_to_remove = ['\r', '\n', '\t', ' ',] )
		
		# extract location information
		location_div = title_right_box.xpath( "./div[@class='tr-line']/div[@class='trl-item2 clearfix']" )
		location_dict = {}
		for one_location in location_div:
			key = one_location.xpath( "./div[@class='lab']/text()" ).extract_first(default="")
			value_list = one_location.xpath( "string(./div[@class='rcont'])" ).extract()
			temp_list = []
			for one_value in value_list:
				temp = CommonClass.clean_string( string = one_value, char_to_remove = [ '\xa0', '\n', '\t', ' ',] )
				temp_list.append( temp.strip('\r') )
				# keep \r
			if 0 < len(key):
				key = CommonClass.clean_string( string = key, char_to_remove = [ '\u2003', '\xa0', '\n', '\t', ' ',] )
				location_dict[ key ] = "___".join( temp_list )

		information_box = response.xpath( "//div[@class='content-item fydes-item']" )
		information_title_list = information_box.xpath( "string(./div[@class='title'])" ).extract()
		information_title = "___".join( information_title_list ) if 0 < len( information_title_list ) else ""
		information1div = information_box.xpath( "./div[@class='cont clearfix']/div[@class='text-item clearfix']" )
		information_dict = {}
		for one_item in information1div:
			key = one_item.xpath( "./span[@class='lab']/text()" ).extract_first(default="")
			value_list = one_item.xpath( "string(./span[@class='rcont'])" ).extract()
			temp_list = []
			for one_value in value_list:
				temp = CommonClass.clean_string( string = one_value, char_to_remove = [ '\xa0', '\n', '\t', ' ',] )
				temp_list.append( temp.strip('\r') )
			if 0 < len(key):
				information_dict[ key ] = "___".join( temp_list )

		community_box1 = response.xpath( "//div[@id='xq_message']" )
		community_title = community_box1.xpath( "./text()" ).extract_first(default="")
		community_title = CommonClass.clean_string( string = community_title, char_to_remove = [ '\xa0', '\n', '\t', ' ',] )
		community_dict = {
			"title": community_title.strip('\r'),
		}
		community_box2 = community_box1.xpath("./following-sibling::div")
		community_box2line1 = community_box2.xpath( "./div[@class='topt clearfix']" )
		line1_list = community_box2line1.xpath( "./div[@class='text-item clearfix']" )
		for one_item in line1_list:
			key = one_item.xpath( "./span[@class='lab']/text()" ).extract_first(default="")
			value_list = one_item.xpath( "string(./span[@class='rcont'])" ).extract()
			if 0 < len(key):
				community_dict[ key ] = "___".join( value_list )

		community_box2line2 = community_box2line1.xpath("./following-sibling::div")
		line2_list = community_box2line2.xpath( "./div[@class='text-item clearfix']" )
		for one_item in line2_list:
			key = one_item.xpath( "./span[@class='lab']/text()" ).extract_first(default="")
			value = one_item.xpath( "./span[@class='rcont ']/text()" ).extract_first(default="")
			if 0 < len(key):
				key = CommonClass.clean_string( string = key, char_to_remove = [ '\xa0', '\n', '\t', ' ',] )
				community_dict[ key ] = CommonClass.clean_string( string = value, char_to_remove = [ '\xa0', '\n', '\t', ' ', '\r', ] )

		community_box2line3 = community_box2line2.xpath("./following-sibling::div")
		community_box2line3key = community_box2line3.xpath( "./div[@class='text-item']/span[@class='lab']/text()" ).extract_first(default="")
		community_box2line3value = community_box2line3.xpath( "string(./div[@class='text-item']/span[@class='rcont'])" ).extract()
		temp_list = []
		for one_value in community_box2line3value:
			temp = CommonClass.clean_string( string = one_value, char_to_remove = [ '\xa0', '\n', '\t', ' ', ] )
			temp = temp.strip('\r')
			if 0 < len(temp):
				temp_list.append( temp )
		if 0 < len( community_box2line3key ):
			community_dict[ community_box2line3key ] = "".join( temp_list )

		text = {
			"title": title.strip(),
			"price": price.strip(),
			"feature": feature_dict,
			"location": location_dict,
			"information": information_dict,
			"community": community_dict,
			"city": city,
			"apt_id": apt_id,
		}
		return text

	def get_apt_id(self, url = ""):
		apt_id = 0
		result_obj = parse.urlparse(url)
		url_list = result_obj.path.split("/")
		while "" in url_list:
			url_list.remove("")
		last_part = url_list[ len(url_list) - 1 ]
		if -1 < last_part.find( ".htm" ):
			temp = last_part.split( "_" )
			if 1 < len(temp):
				temp = f"{temp[1]}"
				search_obj = re.search( r"(\d)+", temp, re.M|re.I )
				if search_obj is not None:
					start = search_obj.span()[0]
					end = search_obj.span()[1]
					if 0 < len( temp[start:end] ):
						apt_id = int( temp[start:end] )
		if 1 > apt_id:
			return f"random{random.randint(10000,99999)}"
		return str( apt_id )

	def log_for_picking_up_the_crawl_break_point( self, page_type = "detailed", response = None ):
		if "detailed" == page_type:
			resume_break_point_file_path = os.path.join( self.log_dir, self.resume_break_point_detailed_file_name )
		else:
			resume_break_point_file_path = os.path.join( self.log_dir, self.resume_break_point_list_file_name )
		try:
			with open( resume_break_point_file_path, "a" ) as f:
				f.write( f"{response.url}\n" )
		except Exception as ex:
			error_msg = f"fail to write response.url into {resume_break_point_file_path}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )

	def parse_detailed_page(self, response = None):
		url = response.url
		result_obj = parse.urlparse( url )
		has_url_error = self.url_contains_error( result_obj_path = result_obj.path )
		if has_url_error:
			return False
			
		page_status = self.save_html( response = response, save100 = True )
		city = self.get_city_from_url( url = url )
		apt_id = self.get_apt_id( url = url )
		text = self.parse_detailed_response_field( response = response, city = city, apt_id = apt_id )
		try:
			loader = ItemLoader( item = FangesfItem(), response = response )
			loader = self.load_items_into_loader( loader = loader, text = text, url = url )
			self.log_for_picking_up_the_crawl_break_point(page_type = "detailed", response = response )
			yield loader.load_item()
		except Exception as ex:
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, fail to load item. Exception = {ex}" )

	def do_nothing_for_debug(self, response = None):
		self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, url = {response.url}" )
		# print( response.body )
		# Inside Method request_proxy_ip of Class ProxyAgent, proxy server returns [{'IP': '49.87.226.131:10749'}] 
		# b'{"REMOTE_ADDR":"49.87.226.131","HTTP_CLIENT_IP":"","HTTP_X_FORWARDED_FOR":"49.87.226.131, 49.87.226.131"}'
		# 2019-06-20 16:28:55 [fangesf] INFO: Inside Method do_nothing_for_debug of Class FangesfSpider, 
		# url = https://www.coursehelper.site/index/index/getHeaders?token=ad89558c89c3394167adbfd1484c8700
		# 2019-06-20 16:28:55 [stdout] INFO: b'{"REMOTE_ADDR":"139.196.200.61","HTTP_CLIENT_IP":"","HTTP_X_FORWARDED_FOR":"139.196.200.61, 139.196.200.61"}'

	def url_contains_i3_page(self, result_obj_path = ""):
		if 1 > len( result_obj_path ):
			return False
		path_fragment_list = result_obj_path.split("/")
		if 1 > len( path_fragment_list ):
			return False
		for one in path_fragment_list:
			if 0 == one.find("i3"):
				return True
			elif 0 == one.find("g2") and 0 < one.find("-i3"):
				# the bedroom url looks like g299-i39
				return True
		return False

	def url_contains_error(self, result_obj_path = ""):
		if 1 > len( result_obj_path ):
			return False
		path_fragment_list = result_obj_path.split("/")
		if 1 > len( path_fragment_list ):
			return False

		# https://sz.esf.fang.com/staticsearchlist/Error/Error404?aspxerrorpath=/house-a013057/i330/i330
		for one in path_fragment_list:
			if -1 < one.find("Error") or -1 < one.find("Error404") or -1 < one.find("staticsearchlist"):
				self.logger.info( f"Error! Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, url = {result_obj_path}" )
				return True

		# http://search.fang.com/captcha-verify/?t=1559927114.963&h=aHR0cHM6Ly9zei5lc2YuZmFuZy5jb20vaG91c2UtYTA5MC1iMDM1NC9nMjU%3D&c=cmE6MTE0LjI1Mi4yMTIuMjEwO3hyaTo7eGZmOg%3D%3D
		for one in path_fragment_list:
			if -1 < one.find("captcha") or -1 < one.find("verify"):
				self.logger.info( f"Need captcha-verify! Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, url = {result_obj_path}" )
				return True

		return False

	def parse_list_page(self, response = None):
		"""
			0 == index_level: https://shaoguan.esf.fang.com/house/i32/ or https://shaoguan.esf.fang.com
			1 == index_level: https://gz.esf.fang.com/house-a072/i34/ or https://gz.esf.fang.com/house-a072/
			2 == index_level: https://gz.esf.fang.com/house-a072-b0627/i35/ or https://gz.esf.fang.com/house-a072-b0627/
			3 == index_level: https://sz.esf.fang.com/house-a090-b0352/g23-i37/ or https://sz.esf.fang.com/house-a090-b0352/g23/
		"""
		result_obj = parse.urlparse( response.url )
		has_url_error = self.url_contains_error( result_obj_path = result_obj.path )
		if has_url_error:
			return False

		page_status = self.save_html( response = response, save100 = False )
		if 1 > page_status:
			pass
			# -2, -1, 0: error_msg has been logged; just pass
		elif 0 < page_status and 101 > page_status and not has_url_error:
			# 1 to 100 also means "index" == page_type
			link_list = self.extract_link_list( response = response )
			if self.debug:
				self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, url = {response.url}; link_list = {link_list}" )
			else:
				self.log_for_picking_up_the_crawl_break_point(page_type = "index", response = response )
				new_url = f"{result_obj.scheme}://{result_obj.netloc}"

				# crawling vertically
				meta_dict = {
					"page_type": "detailed",
					"total_pages": 1,
				}
				if self.use_proxy:
					proxies_dict = self.proxy_ip_pool()
					meta_dict["proxy"] = proxies_dict["http"]
				for one_link in link_list:
					if 0 != one_link.find('/'):
						one_link = f"/{one_link}"
					this_i_url = f"{new_url}{one_link}"
					if this_i_url in self.crawled_detailed_url_list:
						self.logger.info( f"previously crawled {this_i_url}" )
					else:
						self.logger.info( f"requesting {this_i_url}" )
						yield scrapy.Request( url = this_i_url, callback = self.parse_detailed_page, meta = meta_dict, dont_filter = False )
				
				# crawling horizontally
				if 1 < page_status and not self.url_contains_i3_page( result_obj_path = result_obj.path ):
					meta_dict = response.meta
					meta_dict["total_pages"] = page_status
					new_url = f"{new_url}{result_obj.path}"
					if len(new_url) - 1 != new_url.rfind('/'):
						new_url = f"{new_url}/"
					is_bedroom_url = False # https://sz.esf.fang.com/house-a090-b0352/i36/
					if "index_level" in meta_dict.keys() and 3 == int( meta_dict["index_level"] ):
						is_bedroom_url = True
						new_url = new_url.rstrip('/')
						# https://sz.esf.fang.com/house-a090-b0352/g23-i37/
					elif "index_level" in meta_dict.keys() and 0 == int( meta_dict["index_level"] ):
						if 1 > len( result_obj.path ):
							new_url = f"{new_url}house/"
						elif -1 == result_obj.path.find("house"):
							new_url = f"{new_url}house/"
						# this city ONLY has 2 to 99 list pages and there is no need to divide requests into next level
						# therefore 0 == index_level
						# https://shaoguan.esf.fang.com/house/i32/
						
					if self.use_proxy:
						proxies_dict = self.proxy_ip_pool()
						meta_dict["proxy"] = proxies_dict["http"]
					for i in range( page_status - 1 ):
						this_i_url = f"{new_url}-i3{i + 2}" if is_bedroom_url else f"{new_url}i3{i + 2}"
						self.logger.info( f"requesting list page at {this_i_url}" )
						yield scrapy.Request( url = f"{this_i_url}", callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
		elif 101 == page_status and not has_url_error:
			# 101 also means "index" == page_type
			self.log_for_picking_up_the_crawl_break_point(page_type = "index", response = response )
			pointer, link_list, index_level = self.divide_request_into_next_level( response = response )
			# https://sz.esf.fang.com/house-a090-b0352/g23-i37/
			if -1 < pointer:
				# using level3 bedrooms
				meta_dict = {
					"page_type": "index",
					"total_pages": 0,
					"index_level": index_level + 1,
				}
				if self.use_proxy:
					proxies_dict = self.proxy_ip_pool()
					meta_dict["proxy"] = proxies_dict["http"]
				for i in range( len(link_list) - pointer ):
					new_url = self.make_new_url( url = response.url, index_level = index_level, fragment = link_list[ i + pointer ] )
					if 0 < len( new_url ):
						self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, requesting {new_url}; meta_dict = {meta_dict}" )
						yield scrapy.Request( url = new_url, callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
		elif 1001 == page_status and not has_url_error:
			self.parse_detailed_page( response = response )
			# 1001 also means "detailed" == page_type
			# will never reach here because self.parse_detailed_page() is the callback method
			
	def read_and_parse(self, response = None):
		file_list = os.listdir( self.saved_html_dir )
		for one_file in file_list:
			if -1 == one_file.find("index"):
				temp_list = one_file.split("___")
				apt_id = 0
				city = ""
				if 1 < len( temp_list ):
					apt_id = temp_list[1]
					city = temp_list[0]
				url = f"https://{city}.esf.fang.com/chushou/3_{apt_id}.htm" # can also be 16_, 10_, and others
				# https://sz.esf.fang.com/chushou/3_218307566.htm
				html_file_path = os.path.join( self.saved_html_dir, one_file )
				if os.path.isfile(html_file_path):
					doc = None
					with open( html_file_path,'rb') as f:
						# doc = f.read().decode('gb2312', 'ignore')
						doc = f.read().decode('utf-8', 'ignore')
					if doc is None:
						self.logger.error( f"Error: cannot read html file {html_file_path}.")
						continue
					response = Selector( text=doc, type="html" )
					text = self.parse_detailed_response_field( response = response, city = city, apt_id = apt_id )
					try:
						response_for_items = TextResponse( url = url, status = 200, body = bytes(doc, encoding="utf-8") )
						loader = ItemLoader( item = FangesfItem(), response = response_for_items )
						loader = self.load_items_into_loader( loader = loader, text = text, url = url )
						yield loader.load_item()
					except Exception as ex:
						self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, Exception = {ex}" )
					if self.debug:
						break

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
