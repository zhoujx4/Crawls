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
from scrapy.http.cookies import CookieJar

from tt.extensions.commonfunctions import CommonClass
from tt.extensions.proxyagents import ProxyAgent
from land3fang.items import Land3fangItem

class Land3fangSpider(scrapy.Spider):
	"""
		在分布式scrapyd部署之前，为了起多个fangesf进程而采取的临时措施(fangesfp2是本套代码的一个拷贝)。
		sys.exit code == 1 # wrong or missing RUN_PURPOSE
		sys.exit code == 2 # wrong or missing CRAWLED_DIR, SAVED_DETAIL_HTML, or SAVED_GAODE_JASON
		sys.exit code == 3 # fail to get proxy's ip
		sys.exit code == 4 # wrong city_code
		On 20190730 Peter writes this spider upon requests
	"""
	name = "land3fang"

	root_path = ""
	log_dir = ""
	resume_break_point_detailed_file_name = "crawled_detailed_html.log"
	resume_break_point_list_file_name = "crawled_list_html.log"
	crawled_list_url_list = []
	crawled_detailed_url_list = []
	debug = False
	city_list = []
	city_name_dict = {}
	run_purpose = None
	save_every_response = False
	overwrite_today = ""
	crawled_dir = ""
	saved_html_dir = ""
	over34_filename = ""

	custom_settings = CommonClass.get_custom_settings_dict(spider=name)

	proxy_ip_dict = {}
	min_proxy_ip_life_time = 6
	max_proxy_ip_life_time = 180
	use_proxy = False
	proxy_agent = ""

	cookie_string = ""
	cookie_dict = {}
		
	def init_self_attributes(self):
		self.root_path = self.settings.get( "PROJECT_PATH" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )
		self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		self.city_list = self.settings.get( "CITY_LIST", default = [] )
		if 1 > len(self.city_list) and "city" == self.city_name_for_districts:
			self.logger.error( f"missing CITY_LIST ({self.city_list}) setting" )
			sys.exit(1)
		self.city_name_dict = self.settings.get( "CITY_NAME_DICT", default = {} )
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

		if 1 > len( self.crawled_dir ) or 1 > len( self.saved_html_dir ):
			error_msg = f"missing CRAWLED_DIR ({self.crawled_dir}), SAVED_HTML ({self.saved_html_dir}) setting(s)"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			sys.exit(3)

		self.over34_filename = self.settings.get( name = "OVER34_LOG_FILENAME", default="" )

		self.min_proxy_ip_life_time = self.settings.get( name = "MIN_PROXY_LIFE_SPAN", default = 6 )
		self.max_proxy_ip_life_time = self.settings.get( name = "MAX_PROXY_LIFE_SPAN", default = 180 )
		self.use_proxy = self.settings.get( name="HTTPPROXY_ENABLED", default = False )
		self.proxy_agent = self.settings.get( name="PROXY_AGENT", default = "" )

		self.cookie_string = self.settings.get( name = "COOKIE_STRING", default = "" )
		self.cookie_jar = CookieJar()

	def make_dirs(self):
		# even cache is used, we save all html files; here we make these 3 dirs if they do not exist
		if not os.path.isdir( self.crawled_dir ):
			os.makedirs( self.crawled_dir )
		if not os.path.isdir( self.saved_html_dir ):
			os.makedirs( self.saved_html_dir )

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

	def start_requests(self):
		self.init_self_attributes()
		self.make_dirs()
		self.read_crawled_urls()

		if "READ_HTML" == self.run_purpose: # READ_HTML is one kind of debug
			url = 'http://quotes.toscrape.com/page/1/'
			yield scrapy.Request( url = url, callback = self.read_and_parse )
		elif "PRODUCTION_RUN" == self.run_purpose:
			urls = [
				# 广州
				"https://land.3fang.com/market/440100__1______1_1_1.html", # 住宅用地: 26页
				"https://land.3fang.com/market/440100__2______1_1_1.html", # 商业/办公用地: 17页
				"https://land.3fang.com/market/440100__3_2__0_100000__1_1_1.html", # 工业用地, 已成交, 10万平米以下: 32页
				"https://land.3fang.com/market/440100__3_2__100000_500000__1_1_1.html",  # 工业用地, 已成交, 10-50万平米: 4页
				"https://land.3fang.com/market/440100__3_2__500000_100000000__1_1_1.html", # 工业用地, 已成交, 50万平米以上: 1页
				"https://land.3fang.com/market/440100__3_1_____1_1_1.html", # 工业用地, 未成交: 1页
				"https://land.3fang.com/market/440100__3_3_____1_1_1.html", # 工业用地, 流拍: 7页
				"https://land.3fang.com/market/440100__4______1_1_1.html", # 其他用地: 4页

				# # 佛山
				"https://land.3fang.com/market/440600__1_1_____1_1_1.html", # 住宅用地, 未成交: 8页
				"https://land.3fang.com/market/440600__1_2__0_5000__1_1_1.html", # 住宅用地, 已成交, 5千平米以下: 33页
				"https://land.3fang.com/market/440600__1_2__5000_100000__1_1_1.html", # 住宅用地, 已成交, 5千到10万平米: 29页
				"https://land.3fang.com/market/440600__1_2__100000_100000000__1_1_1.html", # 住宅用地, 已成交, 10万平米以上: 6页
				"https://land.3fang.com/market/440600__1_3_____1_1_1.html", # 住宅用地, 流拍: 3页
				"https://land.3fang.com/market/440600__2______1_1_1.html", # 商业用地: 19页
				"https://land.3fang.com/market/440600__3_1_____1_1_1.html", # 工业用地, 未成交: 6页
				"https://land.3fang.com/market/440600__3_2__0_40000__1_1_1.html", # 工业用地, 已成交, 4万平米以下: 32页
				"https://land.3fang.com/market/440600__3_2__40000_100000000__1_1_1.html", # 工业用地, 已成交, 4万平米以上: 12页
				"https://land.3fang.com/market/440600__3_3_____1_1_1.html", # 工业用地, 流拍: 1页
				"https://land.3fang.com/market/440600__4______1_1_1.html", # 其他用地: 3页
			]
			
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
			
			cookie_dict = dict([pair.split("=", 1) for pair in self.cookie_string.split("; ")])
			self.cookie_dict = cookie_dict
			for url in urls:
				url_object = parse.urlparse( url )
				path_list = url_object.path.split("/")
				for one in path_list:
					if -1 == one.find(".html"):
						continue
					city_name = ""
					city_code_list = one.split("_")
					city_code = int(city_code_list[0]) if 0 < len( city_code_list ) else 0
					if 0 < city_code and str(city_code) in self.city_name_dict.keys(): city_name = self.city_name_dict[str(city_code)]
					if 1 > len( city_name ):
						error_msg = f"{city_code} is NOT in self.city_name_dict.keys() ({self.city_name_dict.keys()})"
						self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
						sys.exit(4)
					break
				meta_dict["city"] = city_name
				# cookie_dict = self.change_cookies( cookie_dict )
				yield scrapy.Request( url = url, cookies=cookie_dict, callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
				# yield scrapy.Request( url = url, callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
		elif "READ_CSV_AND_REDO" == self.run_purpose:
			english_city_name = {
				"佛山": "foshan",
				"广州": "guangzhou",
			}
			filename = "tudi_201808.csv"
			csv_file_path = os.path.join( self.crawled_dir, filename )
			url_list = []
			city_list = []
			try:
				with open( csv_file_path, newline="", encoding="utf-8" ) as csvfile:
					file_reader = csv.reader(csvfile) # , delimiter=' ', quotechar='|'
					for row in file_reader:
						if -1 < row[8].find("https:"):
							url_list.append( row[8] )
							city_list.append( row[13] )
			except Exception as ex:
				error_msg = f"cannot read csv file, Exception = {ex}"
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )

			meta_dict = {
				"page_type": "detailed",
				"total_pages": 1,
			}
			self.cookie_dict = dict([pair.split("=", 1) for pair in self.cookie_string.split("; ")])
			if self.use_proxy:
				proxies_dict = self.proxy_ip_pool()
				meta_dict["proxy"] = proxies_dict["http"]

			for index, url in enumerate(url_list):
				chinese_city_name = city_list[index]
				meta_dict["city"] = english_city_name[chinese_city_name]
				yield scrapy.Request( url = url, cookies= self.cookie_dict, callback = self.parse_detailed_page, meta = meta_dict, dont_filter = True )
				break
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

	def change_cookies(self, cookie_dict = {}):
		if "uservisitMarketitem" in cookie_dict.keys():
			item_str = cookie_dict["uservisitMarketitem"]
			item_str = parse.unquote( item_str )
			item_list = item_str.split(",")
			new_str = ""
			for index, one in enumerate(item_list):
				if index > len( item_list ) - 4:
					new_str += f",{one}"
			cookie_dict["uservisitMarketitem"] = parse.quote(new_str)
		return cookie_dict

	def get_total_pages( self, response = None ):
		"""
			/market/440600__4______1_1_3.html
		"""
		total_pages = 0
		if response is None:
			return total_pages
		all_link_list = response.xpath("//div[@id='divAspNetPager']/a/@href").extract()

		total_page_list = []
		for one in all_link_list:
			page = 0
			temp_list = one.split("_")
			for one_fragment in temp_list:
				if -1 < one_fragment.find(".html"):
					page = one_fragment.replace(".html", "")
					total_page_list.append( int( page ) )
					break
		
		if 1 > len( total_page_list ):
			return 1
		return max( total_page_list )

	def get_this_url_page(self, url_obj_path = ""):
		"""
			https://land.3fang.com/market/440600__4______1_1_3.html
			https://land.3fang.com/market/440100__1______1_1_1.html
		"""
		url_list = url_obj_path.split("_")
		for one in url_list:
			if -1 < one.find( ".html" ):
				return int( one.replace(".html", "") )
		return 0

	def make_html_file_name( self, url = "", city = "", page_type = "" ):
		"""
			https://land.3fang.com/market/440600__3_2__40000_100000000__1_1_1.html
			https://land.3fang.com/market/cee05e00-3263-4774-a898-9def16955cb4.html
		"""
		now = datetime.datetime.now()
		html_filename = "{}.html".format( now.strftime("%Y%m%d_%H%M%S") )
		today = now.strftime("%Y%m%d")

		url_obj = parse.urlparse(url)
		url_list = url_obj.path.split("/")
		for one in url_list:
			if -1 < one.find(".html"):
				html_filename = f"{city}__{page_type}__{one}"
				break
		return html_filename

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

	def save_html(self, response = None, save34 = False):
		city = ""
		if response is None or not hasattr( response, "meta" ) or not hasattr( response, "body" ) or not hasattr( response, "url" ):
			if hasattr( response, "url" ):
				error_msg = f"fail to save response.body after requesting {response.url}; response has no body or meta attribute(s)"
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return -1, city
		url = response.url
		meta_dict = response.meta
		page_type = "index"
		total_pages = 0
		city = meta_dict["city"] if "city" in meta_dict.keys() else ""
		if "page_type" in meta_dict.keys():	page_type = meta_dict["page_type"]
		
		if "index" == page_type:
			if "total_pages" in meta_dict.keys(): total_pages = int(meta_dict["total_pages"])
			if 0 == total_pages: total_pages = self.get_total_pages( response = response )
			if 34 < total_pages and not save34:	return 101, city
			html_filename = self.make_html_file_name( url = url, city = city, page_type = page_type )
			html_file_path = os.path.join( self.saved_html_dir, html_filename )
			
		elif "detailed" == page_type:
			html_filename = self.make_html_file_name( url = url, city = city, page_type = page_type )
			html_file_path = os.path.join( self.saved_html_dir, html_filename )
			total_pages = 1001
		
		try:
			with open( html_file_path, "wb" ) as f:
				f.write( response.body )
		except Exception as ex:
			error_msg = f"fail to write response.body into {html_file_path} after requesting {url}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return -2, city
		else:
			if 1 > total_pages:
				error_msg = f"response.body saved after requesting {response.url}; but fail to extract total page number from response.body"
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return total_pages, city # could be 34 when save34 = True

	def extract_link_list( self, response = None ):
		link_list = response.xpath('//dl[@id="landlb_B04_22"]/dd/div[@class="list28_text fl"]/h3/a/@href').extract()
		if 1 > len( link_list ):
			error_msg = f"Fail to extract links from {response.url}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		return link_list

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

	def parse_detailed_response_field(self, response = None, city = "" ):
		text = {}
		if response is None:
			return text
		if "READ_HTML" == self.run_purpose and not isinstance( response, Selector ):
			return text
		information_div = response.xpath("//div[@id='printData1']")

		title = information_div.xpath("./div[@class='tit_box01']/text()").extract_first( default= "" )
		land_id = information_div.xpath("./div[@class='menubox01 mt20']/span[@class='gray2']/text()").extract_first( default= "" )
		province_city = information_div.xpath("string(./div[@class='menubox01 p0515']/div[@class='fl'])").extract()
		province_city = "___".join( province_city )

		if 0 < len( title ): text["title"] = title
		if 0 < len( land_id ): text["land_id"] = land_id
		if 0 < len( province_city ): text["province_city"] = province_city

		key1 = information_div.xpath("./div[@class='p1015']/div[@class='tit_box02 border03']/text()").extract_first( default= "" )
		if "土地基本信息" == key1:
			basic_info = {}
			tr_list1 = information_div.xpath("./div[@class='p1015']/div[@class='tit_box02 border03']/following-sibling::table[@class='tablebox02 mt10']/tbody/tr")
			for index, one_tr in enumerate(tr_list1):
				string_list = one_tr.xpath("string(.)").extract()
				td_list = []
				for one_str in string_list:
					cleaned_str = CommonClass.clean_string( string = one_str, char_to_remove = [ '\xa0', '\n', '\t', ' ',] )
					td_list.append( cleaned_str.strip('\r') )
				basic_info[index] = "___".join( td_list )
			text[key1] = basic_info

		key2 = information_div.xpath("./div[@class='p1015']/div[@class='tit_box02 border03 mt20']/text()").extract_first( default= "" )
		if "土地交易信息" == key2:
			trade_info = {}
			tr_list2 = information_div.xpath("./div[@class='p1015']/div[@class='tit_box02 border03 mt20']/following-sibling::div[@class='banbox']/table[@class='tablebox02 mt10']/tbody/tr")
			for index, one_tr in enumerate(tr_list2):
				string_list = one_tr.xpath("string(.)").extract()
				td_list = []
				for one_str in string_list:
					cleaned_str = CommonClass.clean_string( string = one_str, char_to_remove = [ '\xa0', '\n', '\t', ' ',] )
					td_list.append( cleaned_str.strip('\r') )
				trade_info[index] = "___".join( td_list )
			text[key2] = trade_info

		# 20190730 cannot get 土地评估结果, todo ...
		# evaluation_div = response.xpath("//div[@id='divpg']")
		# key3 = evaluation_div.xpath("./div[@class='tit_box02 border03 mt20']/text()").extract_first( default= "" )
		# if "土地评估结果" == key3:
		# 	evaluation_dict = {}
		# 	tr_list3 = evaluation_div.xpath("./div[@class='table-03']/table[@class='mt5']/tbody/tr")
		# 	for index, one_tr in enumerate( tr_list3 ):
		# 		this_td = one_tr.xpath("./td")
		# 		if this_td is None:
		# 			string_list = one_tr.xpath("string(./th)").extract()
		# 		else:
		# 			td_list = one_tr.xpath("./td")
		# 			string_list = []
		# 			for one_td in td_list:
		# 				unit = one_td.xpath("./text()").extract_first( default= "" )
		# 				amount = one_td.xpath("./span/text()").extract_first( default= "" )
		# 				string_list.append( f"{amount}___{unit}" )
		# 				# this_td_str_list = one_td.xpath("string(.)").extract()
		# 				# string_list.extend( this_td_str_list )
		# 		td_th_list = []
		# 		for one_str in string_list:
		# 			cleaned_str = CommonClass.clean_string( string = one_str, char_to_remove = [ '\xa0', '\n', '\t', ' ',] )
		# 			td_th_list.append( cleaned_str.strip('\r') )
		# 		evaluation_dict[index] = "___".join( td_th_list )
		# 	text[key3] = evaluation_dict

		# evaluation_div = response.xpath("//div[@id='divpg']")
		# key3 = evaluation_div.xpath("./div[@class='tit_box02 border03 mt20']/text()").extract_first( default= "" )
		# if "土地评估结果" == key3:
		# 	evaluation_dict = {}
		# 	th_list3 = evaluation_div.xpath("./div[@class='table-03']/table[@class='mt5']/tbody/tr/th")
		# 	string_list = th_list3.xpath("string(.)").extract()
		# 	evaluation_dict["fields"] = "___".join( string_list )
		# 	tr_list3 = evaluation_div.xpath("./div[@class='table-03']/table[@class='mt5']/tbody/tr")
		# 	row2 = tr_list3[1].xpath("./td")
		# 	row2string = ""
		# 	str1 = row2[0].xpath("./text()").extract_first( default= "" )
		# 	str2 = row2[1].xpath("string(.)").extract()
		# 	str2 = "___".join( str2 )
		# 	str3amount = response.xpath("//span[@id='scbj_bpgj']")
		# 	str3unit = row2[2].xpath("./text()").extract_first( default= "" )
		# 	str4amount = response.xpath("//span[@id='scbj_bSumPrice']")
		# 	str4amount = str4amount.get()
		# 	str3amount = str3amount.get()
		# 	str4unit = row2[3].xpath("./text()").extract_first( default= "" )
		# 	str5 = row2[4].xpath("./a/@href").extract_first( default= "" )
		# 	evaluation_dict[str1] = f"{str2}___{str3amount} {str3unit}___{str4amount} {str4unit}___{str5}"
		# 	row3 = tr_list3[2].xpath("./td")
		# 	row3str = row3.xpath("string(.)").extract()
		# 	evaluation_dict["假设开发法"] = "___".join( row3str )
		# 	text[key3] = evaluation_dict

		if 0 < len( text ): text["city"] = city
		return text

		# {'fields': '\xa0___推出楼面价___评估楼面价___评估总价___操作', '市场比较法': '暂无 元/㎡___ 元/㎡___ 万元___
		# /LandAssessment/b17ea17a-eefa-428b-8b53-461c2bdc67ea.html', '假设开发法': '假设开发法___暂无 元/㎡___元/㎡___万元___[进入评估报告]'}

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
			
		page_status, city = self.save_html( response = response, save34 = True )
		text = self.parse_detailed_response_field( response = response, city = city )
		if isinstance( text, dict ) and 0 < len( text ):
			try:
				loader = ItemLoader( item = Land3fangItem(), response = response )
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

	def url_contains_error(self, result_obj_path = ""):
		if 1 > len( result_obj_path ):
			return False
		path_fragment_list = result_obj_path.split("/")
		if 1 > len( path_fragment_list ):
			return False

		pass
		# do know any anticrawl methods yet

		return False

	def parse_list_page(self, response = None):
		"""
			https://land.3fang.com/market/440600__4______1_1_1.html
		"""
		result_obj = parse.urlparse( response.url )
		has_url_error = self.url_contains_error( result_obj_path = result_obj.path )
		if has_url_error:
			return False

		page_status, city = self.save_html( response = response, save34 = False )
		if 1 > page_status:
			pass
			# -2, -1, 0: error_msg has been logged; just pass
		elif 0 < page_status and 35 > page_status:
			# 1 to 34 also means "index" == page_type
			link_list = self.extract_link_list( response = response )
			if self.debug:
				self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, url = {response.url}; link_list = {link_list}" )
			else:
				self.log_for_picking_up_the_crawl_break_point(page_type = "index", response = response )
				new_url = f"{result_obj.scheme}://{result_obj.netloc}"
				this_cookie = self.cookie_jar.extract_cookies(response, response.request)
				print( this_cookie )

				# crawling vertically
				meta_dict = {
					"page_type": "detailed",
					"total_pages": 1,
					"city": city,
				}
				if self.use_proxy:
					proxies_dict = self.proxy_ip_pool()
					meta_dict["proxy"] = proxies_dict["http"]

				for one_link in link_list:
					if 0 != one_link.find('/'): one_link = f"/{one_link}"
					this_i_url = f"{new_url}{one_link}"
					if this_i_url in self.crawled_detailed_url_list:
						self.logger.info( f"previously crawled {this_i_url}" )
					else:
						self.logger.info( f"requesting {this_i_url}" )
						yield scrapy.Request( url = this_i_url, cookies=self.cookie_dict, callback = self.parse_detailed_page, meta = meta_dict, dont_filter = True )
				
				# crawling horizontally
				if 1 < page_status and 1 == self.get_this_url_page( url_obj_path = result_obj.path ):
					meta_dict = response.meta
					meta_dict["total_pages"] = page_status
					if self.use_proxy:
						proxies_dict = self.proxy_ip_pool()
						meta_dict["proxy"] = proxies_dict["http"]
					for i in range( page_status - 1 ):
						new_path = result_obj.path
						new_path = new_path.replace("1.html", f"{i + 2}.html")
						this_i_url = f"{new_url}{new_path}"
						self.logger.info( f"requesting list page at {this_i_url}" )
						yield scrapy.Request( url = f"{this_i_url}", cookies=self.cookie_dict, callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
		elif 101 == page_status:
			error_msg = f"101: todo ... "
			self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		elif 1001 == page_status:
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
