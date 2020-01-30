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
from shop58.items import Shop58Item

class Shop58Spider(scrapy.Spider):
	"""
		sys.exit code == 1 # wrong or missing RUN_PURPOSE
		sys.exit code == 2 # wrong or missing CRAWLED_DIR, SAVED_DETAIL_HTML, or SAVED_GAODE_JASON
		sys.exit code == 3 # fail to get proxy's ip
		On 20190605 Peter writes this spider upon requests
	"""
	name = "shop58"

	root_path = ""
	log_dir = ""
	over70_filename = ""
	resume_break_point_detailed_file_name = "crawled_detailed_html.log"
	resume_break_point_list_file_name = "crawled_list_html.log"
	crawled_list_url_list = []
	crawled_detailed_url_list = []
	debug = False
	city_list = []
	run_purpose = None
	save_every_response = False
	overwrite_today = ""
	crawled_dir = ""
	saved_html_dir = ""
	gaode_json_dir = ""
	csv_file_path = None

	custom_settings = CommonClass.get_custom_settings_dict(spider=name)

	proxy_ip_dict = {}
	min_proxy_ip_life_time = 6
	max_proxy_ip_life_time = 180
	use_proxy = False

	shop_area_uri_list = [
		"0_20", "20_50", "50_100", "100_200", "200_500", "500_%2A",
	]
		
	def init_self_attributes(self):
		self.root_path = self.settings.get( "PROJECT_PATH" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )
		self.over70_filename = self.settings.get( name="OVER70_LOG_FILENAME", default="" )
		self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		self.city_list = self.settings.get( "CITY_LIST", default = [] )
		if 1 > len(self.city_list):
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
		self.csv_file_path = os.path.join( self.crawled_dir, f"shop58_{self.overwrite_today}.csv" )

		if 1 > len( self.crawled_dir ) or 1 > len( self.saved_html_dir ) or 1 > len( self.gaode_json_dir ):
			error_msg = f"missing CRAWLED_DIR ({self.crawled_dir}), SAVED_HTML ({self.saved_html_dir}), or SAVED_GAODE_JASON ({self.gaode_json_dir}) setting(s)"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			sys.exit(3)

		self.min_proxy_ip_life_time = self.settings.get( name = "MIN_PROXY_LIFE_SPAN", default = 6 )
		self.max_proxy_ip_life_time = self.settings.get( name = "MAX_PROXY_LIFE_SPAN", default = 180 )
		self.use_proxy = self.settings.get( name="HTTPPROXY_ENABLED", default = False )

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
			10000	提取过快，请至少5秒提取一次
		"""
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
		"""
			for resume crawling at a break point
		"""
		resume_break_point_detailed_file_path = os.path.join( self.log_dir, self.resume_break_point_detailed_file_name )
		try:
			with open( resume_break_point_detailed_file_path, "r", encoding="utf-8" ) as log_file:
				self.crawled_detailed_url_list = log_file.readlines()
				while "" in self.crawled_detailed_url_list:
					self.crawled_detailed_url_list.remove("")
		except Exception as ex:
			error_msg = f"fail to read {resume_break_point_detailed_file_path}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )

	def start_requests(self):
		self.init_self_attributes()
		self.make_dirs()
		self.read_crawled_urls()

		if "READ_HTML" == self.run_purpose: # READ_HTML is one kind of debug
			url = 'http://quotes.toscrape.com/page/1/'
			yield scrapy.Request( url = url, callback = self.read_and_parse )
		elif "PRODUCTION_RUN" == self.run_purpose:
			city_list = self.settings.get( "CITY_LIST", default = [] )
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
					urls.append( f"https://{city}.58.com/shangpu/" )
			
			meta_dict = {
				"page_type": "index",
				"total_pages": 0,
				"index_level": 0,
			}
			if self.use_proxy:
				proxies_dict = self.proxy_ip_pool()
				if 1 > len( proxies_dict):
					sys.exit(3)
				meta_dict["proxy"] = proxies_dict["http"]
			for url in urls:
				yield scrapy.Request( url = url, callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
		elif "CHECK_PROXY_IP" == self.run_purpose:
			now = int(time.time())
			token = f"Guangzhou{str(now)}"
			m = hashlib.md5()  
			m.update( token.encode(encoding = 'utf-8') )
			urls = [
				f"https://www.coursehelper.site/index/index/getHeaders?token={m.hexdigest()}",
			]
			
			proxies_dict = ProxyAgent.get_xunlian_proxy_dict(headers = {}, params_for_proxy_ip={}, setup_xunlian_dict = {}, need_setup_xunlian = False, logger=self.logger )
			if 0 < len( proxies_dict):
				meta_dict = {
					"proxy": proxies_dict["http"]
				}
				for url in urls:
					yield scrapy.Request( url=url, callback=self.do_nothing_for_debug, meta = meta_dict )
			else:
				self.logger.error( f"Error! No proxy ip returns. {proxies_dict}" )
		elif "SAVE_ONE_HTML" == self.run_purpose:
			url = "https://gz.58.com/shangpu/"
			meta_dict = {
				"page_type": "index",
				"total_pages": 0,
				"index_level": 0,
			}
			yield scrapy.Request( url = url, callback = self.do_nothing_for_debug, meta = meta_dict, dont_filter = True )
		else:
			urls = [
				"http://quotes.toscrape.com/page/1/",
				"http://quotes.toscrape.com/page/2/",
			]
			for url in urls:
				yield scrapy.Request( url=url, callback=self.do_nothing_for_debug )

	def remove_url_page_part(self, url = "", add_query = True ):
		"""
			this version ignore url_obj.fragment and url_obj.params
		"""
		new_url = url
		url_obj = parse.urlparse(url)
		if hasattr( url_obj, "path" ):
			url_list = url_obj.path.split("/")
			path_changed = False
			for one in url_list:
				if 0 == one.find("pn"):
					url_list.remove( one )
					path_changed = True
			if path_changed:
				new_path = "/".join( url_list )
				new_url = f"{url_obj.scheme}://{url_obj.netloc}"
				new_url = new_url.rstrip("/")
				if 0 < len( new_path ):
					new_path = new_path.lstrip("/")
					new_url = f"{new_url}/{new_path}"

				if hasattr( url_object, "query" ) and 0 < len( url_obj.query ) and add_query:
					new_url = f"{new_url}{ url_obj.query }"
		return new_url

	def add_url_page_part( self, old_url = "", page = 2 ):
		"""
			this version ignore url_obj.fragment and url_obj.params
		"""
		url_obj = parse.urlparse(old_url)
		new_url = f"{url_obj.scheme}://{url_obj.netloc}"
		if not hasattr( url_obj, "path" ) or 1 > len(url_obj.path):
			new_path = f"pn{page}"
		else:
			temp_list = []
			url_list = url_obj.path.split("/")
			for one in url_list:
				if 0 == one.find("pn"):
					continue
				if 0 < len( one ):
					temp_list.append( one )
			temp_list.append( f"pn{page}" )
			new_path = "/".join( temp_list )
		new_url = f"{url_obj.scheme}://{url_obj.netloc}"
		new_url = new_url.rstrip("/")
		new_path = new_path.lstrip("/")
		new_url = f"{new_url}/{new_path}"
		new_url = new_url.rstrip("/")

		if hasattr( url_obj, "query" ) and 0 < len( url_obj.query ):
			new_url = f"{new_url}/?{ url_obj.query }"
		return new_url

	def get_page_from_url( self, url = "" ):
		page_num = 0
		url_obj = parse.urlparse(url)
		if hasattr( url_obj, "path" ):
			url_list = url_obj.path.split("/")
			for one in url_list:
				if 0 == one.find("pn"):
					page_num = CommonClass.find_digits_from_str( string = one, return_all = False )
		return int(page_num)

	def get_total_pages( self, response = None ):
		total_pages = 0
		if response is None:
			return total_pages

		page_list = response.xpath("//div[@class='content-side-left']/div[@class='pager']/a/@href").extract()
		for one in page_list:
			this_url_page_num = self.get_page_from_url( url = one )
			if total_pages < this_url_page_num:
				total_pages = this_url_page_num

		if 1 > total_pages:
			error_msg = f"fail to extract last page number ({page_list}) from {response.url} or this url has ONLY one page"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		return total_pages

	def get_city_from_url(self, url = ""):
		city = ""
		result_obj = parse.urlparse(url)
		if -1 < result_obj.netloc.find("58.com"):
			temp2_list = result_obj.netloc.split(".")
			if 3 == len( temp2_list ):
				city = temp2_list[0]
		return city

	def get_page_area_district_from_url(self, url_object = None ):
		"""
			https://fs.58.com/shangpucz/
			https://gz.58.com/shangpu/
			https://gz.58.com/tianhe/shangpucz/pn3/?area=20_50
			https://fs.58.com/foshan/shangpucz/pn2/			# foshan == 佛山周边，与禅城、高明、三水等同级
			https://gz.58.com/shangpucz/pn3/
			https://fs.58.com/shangpu/38143746902823x.shtml
		"""
		page = "1"
		district = ""
		shop_area = ""
		detailed_page = False
		if url_object is not None and hasattr( url_object, "netloc" ) and -1 < url_object.netloc.find("58.com"):
			# parse query
			has_shop_area = True
			if not hasattr( url_object, "query" ) or 1 > len( url_object.query ):
				has_shop_area = False
			if has_shop_area:
				query_dict = parse.parse_qs( url_object.query )
				if "area" in query_dict.keys() and isinstance( query_dict["area"], list ) and 0 < len( query_dict["area"]):
					shop_area = query_dict["area"][0]
			
			# parse path
			if hasattr( url_object, "path" ):
				url_list = url_object.path.split("/")
				temp_list = []
				for one in url_list:
					if 0 < len( one ) and -1 == one.find("shangpucz") and -1 == one.find("shangpu") and -1 == one.find("pn"):
						temp_list.append(one)
					elif -1 < one.find("pn"):
						page = CommonClass.find_digits_from_str( string = one, return_all = False )
					elif -1 < one.find(".shtml"):
						detailed_page = True
				if not detailed_page and 1 == len( temp_list ):
					district = temp_list[0]
		if detailed_page:
			page = "0"
		return (page, district, shop_area)

	def make_html_file_name( self, url = "", city = "" ):
		"""
			https://fs.58.com/shangpucz/
			https://gz.58.com/shangpu/
			https://gz.58.com/tianhe/shangpucz/pn3/?area=20_50
			https://fs.58.com/foshan/shangpucz/pn2/
			https://gz.58.com/shangpucz/pn3/
			https://fs.58.com/shangpu/38143746902823x.shtml
		"""
		now = datetime.datetime.now()
		html_filename = "{}.html".format( now.strftime("%Y%m%d_%H%M%S") )
		today = now.strftime("%Y%m%d")

		result_obj = parse.urlparse(url)
		url_list = result_obj.path.split("/")
		while "" in url_list:
			url_list.remove("")

		detail_page = False
		last_part = url_list[ len(url_list) -1 ] if 0 < len( url_list ) else ""
		if -1 < last_part.find( ".shtml" ):
			detail_page = True
			# https://fs.58.com/shangpu/38143746902823x.shtml
			shop_id = last_part.rstrip( ".shtml" )
			html_filename = f"{city}___{shop_id}___{today}.html"
		elif -1 < result_obj.netloc.find("58.com") and 1 == len( url_list ) and url_list[0] in ["shangpucz", "shangpu",]:
			# list page #1: https://fs.58.com/shangpucz/
			html_filename = f"{city}___all___all___index1___{today}.html"
		else:
			page, district, shop_area = self.get_page_area_district_from_url( url_object = result_obj )
			if -1 < shop_area.find("500_"):
				shop_area = "over500"

			if 0 < len( district ) and 0 < len( shop_area ):
				html_filename = f"{city}___{district}___{shop_area}___index{page}___{today}.html"
			elif 0 < len( district ):
				html_filename = f"{city}___{district}___all___index{page}___{today}.html"
			elif 0 < len( shop_area ):
				html_filename = f"{city}___all___{shop_area}___index{page}___{today}.html"
			else:
				html_filename = f"{city}___all___all___index{page}___{today}.html"
		return (detail_page, html_filename)

	def get_shop_id(self, url = ""):
		shop_id = f"random{random.randint( 10000, 99999 )}"
		url_obj = parse.urlparse(url)
		if hasattr( url_obj, "path" ):
			url_list = url_obj.path.split("/")
			for one in url_list:
				if -1 < one.find(".shtml"):
					shop_id = one.rstrip( ".shtml" )
		return shop_id

	def save_html(self, response = None, save70 = False):
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

			if 69 < total_pages and not save70:
				return 101
			detail_page, html_filename = self.make_html_file_name( url = url, city = city )
			html_file_path = os.path.join( self.saved_html_dir, html_filename )
			
		elif "detailed" == page_type:
			total_pages = 1001
			today = datetime.datetime.now().strftime("%Y%m%d")
			shop_id = self.get_shop_id( url = url )
			html_filename = f"{city}___{shop_id}___{today}.html"
			html_file_path = os.path.join( self.saved_html_dir, html_filename )
		
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
			return total_pages # could be 70 when save70 == True

	def divide_request_into_next_level( self, response = None ):
		"""
		# returns:
			(-1, [], -1): wrong response object
			(-2, [], 2): already using shop area as level 2, currently we only have levels up to 2
			(-3, [], -1): this response.url is already page #2 or more
			(-4, [], -1): this page is a detailed page
			(-11, [], index_level): fail to extract links from response.body
			(-12, [], index_level): same as (-2, [], 2)
			(-13, [], index_level): wrong parameter (index_level)
			(pointer, district_list, index_level): 0 == pointer; district_list is a []; index_level is int and in [0, 1, 2]
			0 == index_level: this url is for whole city like guangzhou, foshan, or shenzhen
			1 == index_level: this url is for one district like tianhe, baiyun, panyu, or others in guangzhou
			2 == index_level: this url is for one shop_area size listed in self.shop_area_uri_list
			https://fs.58.com/shangpucz/
			https://gz.58.com/shangpu/
			https://gz.58.com/tianhe/shangpucz/pn3/?area=20_50
			https://fs.58.com/foshan/shangpucz/pn2/
			https://gz.58.com/shangpucz/pn3/
		"""
		if response is None or not hasattr( response, "meta" ) or not hasattr( response, "body" ) or not hasattr( response, "url" ):
			error_msg = f"meta = {hasattr( response, 'meta' )}; body = {hasattr( response, 'body' )}; url = {hasattr( response, 'url' )}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return (-1, [], -1)
		url = response.url
		url_obj = parse.urlparse(url)
		page, district, shop_area = self.get_page_area_district_from_url(url_object = url_obj)

		if 0 < len(shop_area):
			page_status = self.save_html( response = response, save70 = True )
			self.write_log( content = f"{response.url}", logfilename = self.over70_filename, content_only = True)
			return (-2, [], 2)
		if 1 < int( page ):
			page_status = self.save_html( response = response, save70 = True )
			return (-3, [], -1)
		elif 0 == int( page ):
			return (-4, [], -1)

		index_level = self.get_index_level( response = response, district = district )

		pointer, link_list = self.extract_this_level_options( response = response, index_level = index_level, district = district )
		if pointer in [-11, -12,]:
			page_status = self.save_html( response = response, save70 = True )
			self.write_log( content = f"{response.url}", logfilename = self.over70_filename, content_only = True)
		return ( pointer, link_list, index_level )

	def get_index_level(self, response = None, district = ""):
		meta_dict = response.meta
		index_level = 0
		if "index_level" in meta_dict.keys():
			index_level = int( meta_dict["index_level"] )

		url_obj = parse.urlparse( response.url )
		query_dict = url_obj.query if hasattr( url_obj, "query" ) else {}
		if 0 < len( query_dict ):
			query_dict = parse.parse_qs( query_dict )

		# district and area have higher priority than index_level
		if 0 < len( query_dict ) and "area" in query_dict.keys():
			if 2 != index_level:
				index_level = 2
		elif 0 < len( district ) and 1 != index_level:
			error_msg = f"index_level {index_level} != ({district})"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			index_level = 1
		elif 0 == len( district ) and 0 != index_level:
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {index_level} is not 0" )
			index_level = 0

		return index_level

	def make_new_url(self, parent_level_url = "", index_level = 0, fragment = "" ):
		"""
			make one child url according to parent url
			https://fs.58.com/shangpucz/
			https://gz.58.com/shangpu/
			https://gz.58.com/tianhe/shangpucz/pn3/?area=20_50
			https://fs.58.com/foshan/shangpucz/pn2/			# foshan == 佛山周边，与禅城、高明、三水等同级
			https://gz.58.com/shangpucz/pn3/
		"""
		parent_url_obj = parse.urlparse(parent_level_url)
		child_url = f"{parent_url_obj.scheme}://{parent_url_obj.netloc}"
		child_url = child_url.rstrip("/")
		if 1 == index_level: # it is parent's index_level
			return f"{child_url}/{parent_url_obj.path.lstrip('/')}?area={fragment}"
		elif 0 == index_level:
			return f"{child_url}/{fragment.strip('/')}/shangpucz/"
		else:
			return ""

	def extract_district_from_url_paths(self, district_list = []):
		"""
			/shangpucz/
			/tianhe/shangpucz/
			/haizhu/shangpucz/
		"""
		return_list = []
		for one_link in district_list:
			url_list = one_link.split("/")
			good_url_list = []
			for good_url in url_list:
				if 0 < len( good_url ) and -1 == good_url.find("shangpucz") and -1 == good_url.find("shangpu"):
					# and -1 == good_url.find("pn") and -1 == one.find(".shtml"):
					good_url_list.append(good_url)
			if 1 == len( good_url_list ):
				return_list.append( good_url_list[0] )
		return return_list

	def extract_this_level_options(self, response = None, index_level = 0, district = "" ):
		"""
		# returns:
			( 0, [a list has one element or more] )
			( -11, [] ): fail to extract links from response.body
			( -12, [] ): already 2 == index_level
			( -13, [] ): wrong parameter ( index_level )
		"""
		district_list = []
		if 0 == index_level:
			district_dl = response.xpath('//div[@class="filter-wrap"]/dl[@class="secitem"]')
			for one_district in district_dl:
				dl_dtitle = one_district.xpath("./dt/text()").extract_first( default = "" )
				if 0 == dl_dtitle.find("区域："):
					break
			district_list = one_district.xpath( "./dd/a/@href" ).extract()
			if 0 < len( district_list ):
				district_list = self.extract_district_from_url_paths( district_list = district_list )
			if 0 < len( district_list ):
				return ( 0, district_list )
			error_msg = f"fail to extract links from response.body after requesting {response.url}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return ( -11, [] )
		elif 1 == index_level:
			return ( 0, self.shop_area_uri_list )
		elif 2 == index_level:
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, 2 == index_level; we will NOT divide further" )
			return (-12, [])
		else:
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, wrong index_level ({index_level})" )
			return (-13, [])

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

	def extract_shop_id_from_href( self, shop_id = "", use_logr = False):
		"""
		# href:
			https://jxjump.58.com/service?target=FCADV8oV3os7xtAj_6pMK7rUlr7DdRMx8H_54olt8EXOWkK_Zpk1zEffDjhGKDukKaSGKEtf3gzeNV-\
			jc68R330iX4JeiOAQ9mxZIx_7k2_EqtKoFph2NZi5EUpVl9S607kui9wZ5vFL9FjgOWSrSlIBohzi3WsLQSp_Rr-QuiAazy31jEubeh76kg5T_\
			uVyVN1UCEVsUjMvAnmEU0sZOrGXZEsuraI5DWpE1qXSASL8rH4cOWSrSlIBoh7ifevBw4N33&pubid=75911118&apptype=0&psid=161954686204511925276830641&\
			entinfo=38284513452802_0&cookie=%7C%7C%7C&amp;fzbref=0&amp;key&params=busitime^desc

		# logr:
			z_2_33120284640267_38420286183181_1_2_sortid:613502485@postdate:1560301497000
			gz_2_55687810204183_36683482092955_sortid:599933703@postdate:1560268805000@ses:busitime^desc@pubid:76309565
		"""
		shop_id_str = ""
		if use_logr:
			seen_sortid = False
			if isinstance(shop_id, str):
				temp_list = shop_id.split("_")
				if 0 < len( temp_list ):
					temp_list.reverse()
					for one in temp_list:
						if 0 == one.find( "sortid" ):
							seen_sortid = True
						if seen_sortid and 14 == len( one ):
							return one
		else:
			url_obj = None
			if isinstance( shop_id, str ):
				url_obj = parse.urlparse(shop_id)
			if hasattr( url_obj, "query" ):
				query_dict = parse.parse_qs( url_obj.query )
				if isinstance( query_dict, dict) and "entinfo" in query_dict.keys():
					shop_id_str = query_dict["entinfo"]
					if isinstance( shop_id_str, list ) and 0 < len( shop_id_str ):
						shop_id_str = shop_id_str[0]
					if isinstance( shop_id_str, str ) and -1 < shop_id_str.find("_"):
						temp_list = shop_id_str.split("_")
						shop_id_str = temp_list[0]
		return shop_id_str

	def parse_list_response_field(self, response = None, city = "" ):
		text_list = []
		if response is None:
			return text
		if "READ_HTML" == self.run_purpose and not isinstance( response, Selector ):
			return text

		shops = response.xpath('//div[@class="content-wrap"]/div[@class="content-side-left"]/ul[@class="house-list-wrap"]/li[@logr]')
		for one_shop in shops:
			try:
				shop_id = one_shop.xpath("./div[@class='list-info']/h2[@class='title']/a/@href").extract_first(default='')
				shop_id = self.extract_shop_id_from_href( shop_id = shop_id, use_logr = False )
				if 1 > len( shop_id ):
					shop_id = one_shop.xpath("./@logr").extract_first(default='')
					shop_id = self.extract_shop_id_from_href( shop_id = shop_id, use_logr = True )
				title = one_shop.css('div.list-info h2.title a span.title_des::text').extract_first(default='')
				baseinfo_list = one_shop.css('div.list-info p.baseinfo')
				description = ""
				baseinfo_items = []
				address = ""
				for index, onelist in enumerate(baseinfo_list):
					temp = onelist.css("span::text").extract()
					if 0 < len( temp ):
						baseinfo_items += temp
						if index + 1 == len( baseinfo_list ):
							address = temp[ len(temp) - 1 ]
				if 0 < len(baseinfo_items):
					description = "___descr___".join(baseinfo_items)
				
				tags = ""
				tag_list = one_shop.xpath("./div[@class='list-info']/p[@class='tag-wrap']/span/text()").extract()
				if 0 < len( tag_list ):
					tags = "___tags___".join(tag_list)
				price_box = one_shop.css('div.price')
				price_sum = price_box.css('p.sum b::text').extract_first(default='')
				price_sum_unit = price_box.css('p.sum span::text').extract_first(default='')
				unitprice = price_box.css('p.unit span::text').extract_first(default='')
				unitprice_unit_list = price_box.css('p.unit::text').extract()
				unitprice_unit = unitprice_unit_list[len(unitprice_unit_list) - 1].strip() if 0 < len(unitprice_unit_list) else ""
				text = {
					"shop_id": shop_id,
					"city": city,
					"title": title.strip(),
					"description": description.strip(),
					"address": address,
					"tags": tags,
					"price_sum": price_sum.strip(),
					"price_sum_unit": price_sum_unit.strip(),
					"unitprice": unitprice.strip(),
					"unitprice_unit": unitprice_unit.strip(),
				}
				text_list.append( text )
			except Exception as ex:
				error_msg = f"Error happened during parsing. Exception = {ex}; one_shop = {one_shop}"
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
				continue
		return text_list

	def parse_detailed_page(self, response = None):
		self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, todo..." )
		pass

	def do_nothing_for_debug(self, response = None):
		self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, url = {response.url}" )
		print( response.body )
		# Inside Method request_proxy_ip of Class ProxyAgent, proxy server returns [{'IP': '49.87.226.131:10749'}] 
		# b'{"REMOTE_ADDR":"49.87.226.131","HTTP_CLIENT_IP":"","HTTP_X_FORWARDED_FOR":"49.87.226.131, 49.87.226.131"}'

	def url_contains_error(self, url_obj = ""):
		"""
			we do not know any anticrawl method by 58.com yet
		"""
		if hasattr( url_obj, "path" ):
			pass

		return False

	def make_next_pages_url_from_page_one(self, url = "", index_level_int = 0, page_number_int = 0 ):
		urls = []
		if 2 > page_number_int or 0 > index_level_int or 2 < index_level_int:
			return urls

		page = self.get_page_from_url( url = url )
		if 1 < page:
			return urls # we ONLY do this at Page 1
		elif 1 == page:
			# url contains /pnxxx/ part; then remove it
			new_url = self.remove_url_page_part( url = url )
		else:
			new_url = url.rstrip("/")

		if 2 > index_level_int:
			# 0 == index_level_int: https://gz.58.com/shangpucz/pn3/
			# 1 == index_level_int: https://fs.58.com/foshan/shangpucz/pn2/
			for i in range( page_number_int - 1 ):
				urls.append( self.add_url_page_part(old_url = url, page = (i + 2) ) )
		else:
			# https://gz.58.com/tianhe/shangpucz/pn3/?area=20_50
			for i in range( page_number_int - 1 ):
				urls.append( self.add_url_page_part(old_url = url, page = (i + 2) ) )
		return urls

	def parse_list_page(self, response = None):
		page_status = self.save_html( response = response, save70 = False )
		
		url_obj = parse.urlparse( response.url )
		no_url_error = self.url_contains_error( url_obj = url_obj )
		load_this_page_items = False

		if 1 > page_status:
			pass
			# -2, -1, 0: error_msg has been logged; just pass
		elif 0 < page_status and 101 > page_status and not no_url_error:
			# 1 to 70 also means "index" == page_type
			load_this_page_items = True
			if 1 < page_status: # ONLY reponsed html having total page more than 1 will go further
				page, district, shop_area = self.get_page_area_district_from_url(url_object = url_obj)
				if 1 == int( page ):
					# ONLY do this on Page #1
					index_level = self.get_index_level( response = response, district = district )
					urls = self.make_next_pages_url_from_page_one( url = response.url, index_level_int = index_level, page_number_int = page_status )
					meta_dict = {
						"page_type": "index",
						"total_pages": page_status,
						"index_level": index_level,
					}
					for one_url in urls:
						yield scrapy.Request( url = one_url, callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
		elif 101 == page_status and not no_url_error:
			# 101 also means "index" == page_type
			pointer, link_list, index_level = self.divide_request_into_next_level( response = response )
			if pointer in [-2, -3, -11, -12,]:
				load_this_page_items = True
			elif -1 < pointer:
				# going to request all children level list page
				meta_dict = {
					"page_type": "index",
					"total_pages": 0,
					"index_level": index_level + 1,
				}
				if self.use_proxy:
					proxies_dict = self.proxy_ip_pool()
					meta_dict["proxy"] = proxies_dict["http"]
				for i in range( len(link_list) - pointer ):
					new_url = self.make_new_url( parent_level_url = response.url, index_level = index_level, fragment = link_list[ i + pointer ] )
					if 0 < len( new_url ):
						self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, requesting {new_url}; meta_dict = {meta_dict}" )
						yield scrapy.Request( url = new_url, callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
		elif 1001 == page_status and not no_url_error:
			self.parse_detailed_page( response = response )
			# 1001 also means "detailed" == page_type
			# will never reach here because self.parse_detailed_page() is the callback method

		if load_this_page_items:
			url = response.url
			city = self.get_city_from_url( url = url )
			text_list = self.parse_list_response_field( response = response, city = city )
			try:
				for text in text_list:
					loader = ItemLoader( item = Shop58Item(), response = response )
					loader = self.load_items_into_loader( loader = loader, text = text, url = url )
					yield loader.load_item()
			except Exception as ex:
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, fail to load item. Exception = {ex}" )
			
	def read_and_parse(self, response = None):
		self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, url = {response.url}. under developing..." )
		pass
		# file_list = os.listdir( self.saved_html_dir )
		# for one_file in file_list:
		# 	if -1 == one_file.find("index"):
		# 		temp_list = one_file.split("___")
		# 		apt_id = 0
		# 		city = ""
		# 		if 1 < len( temp_list ):
		# 			apt_id = temp_list[1]
		# 			city = temp_list[0]
		# 		url = f"https://{city}.esf.fang.com/chushou/3_{apt_id}.htm"
		# 		html_file_path = os.path.join( self.saved_html_dir, one_file )
		# 		if os.path.isfile(html_file_path):
		# 			doc = None
		# 			with open( html_file_path,'rb') as f:
		# 				# doc = f.read().decode('gb2312', 'ignore')
		# 				doc = f.read().decode('utf-8', 'ignore')
		# 			if doc is None:
		# 				self.logger.error( f"Error: cannot read html file {html_file_path}.")
		# 				continue
		# 			response = Selector( text=doc, type="html" )
		# 			text_list = self.parse_list_response_field( response = response, city = city, apt_id = apt_id )
		# 			try:
		# 				for text in text_list:
		# 					loader = ItemLoader( item = Shop58Item(), response = response )
		# 					loader = self.load_items_into_loader( loader = loader, text = text, url = url )
		# 					yield loader.load_item()
		# 			except Exception as ex:
		# 				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, fail to load item. Exception = {ex}" )
		# 			if self.debug:
		# 				break

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
