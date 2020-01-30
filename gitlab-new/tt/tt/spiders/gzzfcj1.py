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
from gzzfcj1.items import Gzzfcj1Item

class Gzzfcj1Spider(scrapy.Spider):
	"""
	爬取广州阳光家缘列表页面给湘龙，不过由于只有广州有这些数据，决定本网站仅仅是备份；以后有需要再爬取详情页面
		revision 20190806
	"""
	name = "gzzfcj1"

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
	base_url = ""

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
		self.run_purpose = self.settings.get( name = "RUN_PURPOSE", default=None )
		if self.run_purpose is None:
			self.logger.error( f"missing RUN_PURPOSE ({self.run_purpose}) setting" )
			sys.exit(1)
		self.save_every_response = self.settings.get( name = "SAVE_EVERY_RESPONSE", default = False )
		self.overwrite_today = self.settings.get( "OVERWRITE_TODAY", default = "" )
		if not hasattr(self, "overwrite_today") or 1 > len( self.overwrite_today ) or self.overwrite_today is None:
			self.overwrite_today = datetime.datetime.now().strftime("%Y%m%d")

		# set all paths
		self.crawled_dir = self.settings.get( name = "CRAWLED_DIR", default = "" )
		self.saved_html_dir = self.settings.get( name = "SAVED_HTML", default="" )
		self.base_url = self.settings.get( name = "BASE_URL", default="" )

		if 1 > len( self.crawled_dir ) or 1 > len( self.saved_html_dir ):
			error_msg = f"missing CRAWLED_DIR ({self.crawled_dir}), SAVED_HTML ({self.saved_html_dir}) setting(s)"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			sys.exit(3)

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
				# 只有广州有阳光家缘
				"http://zfcj.gz.gov.cn/data/Laho/ProjectSearch.aspx",
			]
			
			meta_dict = {
				"page_type": "index",
				"page": 1,
				"total_pages": 468,
			}
			if self.use_proxy:
				proxies_dict = self.proxy_ip_pool()
				if 1 > len( proxies_dict):
					sys.exit(3)
				meta_dict["proxy"] = proxies_dict["http"]
			
			for url in urls:
				# yield scrapy.Request( url = url, cookies=cookie_dict, callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
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
		all_span_text_list = response.xpath("//span[@id='pe100_page_项目信息查询列表']/div[@class='pager']/span/text()").extract()
		# 共7013/共468页
		for one_text in all_span_text_list:
			if -1 == one_text.find("共"):
				continue
			page = 0
			fragment_list = one_text.split("/")
			for one_fragment in fragment_list:
				if -1 < one_fragment.find("页"):
					page = one_fragment.replace("页", "")
					page = page.replace("共", "")
					return int( page )
		return 0

	def make_html_file_name( self, url = "", city = "", page_type = "" ):
		"""
			pass
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

	def save_html(self, response = None ):
		page_type = "index"
		total_pages = 0
		page = 0

		if response is None or not hasattr( response, "meta" ) or not hasattr( response, "body" ) or not hasattr( response, "url" ):
			if hasattr( response, "url" ):
				error_msg = f"fail to save response.body after requesting {response.url}; response has no body or meta attribute(s)"
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return -1, page
		url = response.url
		meta_dict = response.meta

		if "page_type" in meta_dict.keys():	page_type = meta_dict["page_type"]
		if "page" in meta_dict.keys():	page = meta_dict["page"]
		
		if "index" == page_type:
			if "total_pages" in meta_dict.keys(): total_pages = int(meta_dict["total_pages"])
			if 0 == total_pages: total_pages = self.get_total_pages( response = response )
			html_filename = f"realestate___list{page}.html"
			html_file_path = os.path.join( self.saved_html_dir, html_filename )
			
		elif "detailed" == page_type:
			html_filename = self.make_html_file_name( url = url, page_type = page_type )
			html_file_path = os.path.join( self.saved_html_dir, html_filename )
			total_pages = 100001
		
		try:
			with open( html_file_path, "wb" ) as f:
				f.write( response.body )
		except Exception as ex:
			error_msg = f"fail to write response.body into {html_file_path} after requesting {url}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return -2, page
		else:
			if 1 > total_pages:
				error_msg = f"response.body saved after requesting {response.url}; but fail to extract total page number from response.body"
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return total_pages, page

	def extract_link_list( self, response = None ):
		record_list = []
		tr_list = response.xpath('//table[@class="resultTableC"]/tbody/tr')
		for one_tr in tr_list:
			try:
				detailed_page_link = one_tr.xpath('./tr/td/a/@href').extract_first(default = "")
				detailed_page_link = CommonClass.clean_string( string = detailed_page_link, char_to_remove = ['\r', '\n', '\t', ' ',] )
				td_list = one_tr.xpath('./td')
				value_list = []
				for one_td in td_list:
					value_list.append( one_td.xpath("./a/text()").extract_first(default = "") )
				
				# 检查这7个字段是否都是空字符串
				if 7 == len( value_list ):
					not_empty = False
					for one_value in value_list:
						if isinstance( one_value, str ) and 0 < len( one_value ):
							not_empty = True
							break
				if 7 == len( value_list ) and not_empty:
					this_record = {
						"序号": value_list[0],
						"项目名称": value_list[1],
						"开发商": value_list[2],
						"预售证": value_list[3],
						"项目地址": value_list[4],
						"住宅已售套数": value_list[5],
						"住宅未售套数": value_list[6],
						"详情链接": detailed_page_link,
					}
					record_list.append( this_record )
				elif 7 != len( value_list ):
					error_msg = f"value_list ({value_list}) has length other than 7"
					self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
				
			except Exception as ex:
				error_msg = f"xpath error! Exception = {ex}"
				self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		if 1 > len( record_list ):
			error_msg = f"Fail to extract links from {response.url}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		return record_list

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
			
		total_pages, page = self.save_html( response = response )
		text = self.parse_detailed_response_field( response = response, city = city )
		if isinstance( text, dict ) and 0 < len( text ):
			try:
				loader = ItemLoader( item = Gzzfcj1Item(), response = response )
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

	def url_contains_error(self, url_obj_path = ""):
		if 1 > len( url_obj_path ):
			return False
		path_fragment_list = url_obj_path.split("/")
		if 1 > len( path_fragment_list ):
			return False

		pass
		# do know any anticrawl methods yet

		return False

	def parse_list_page(self, response = None ):
		url_obj = parse.urlparse( response.url )
		has_url_error = self.url_contains_error( url_obj_path = url_obj.path )
		if has_url_error:
			return False

		total_pages, page = self.save_html( response = response )
		print( f"total_pages = {total_pages}, page = {page}; url = {response.url}" )

		if 1 > total_pages:
			pass
			# -2, -1, 0: error_msg has been logged; just pass
		elif 100001 == total_pages:
			self.parse_detailed_page( response = response )
		else:
			link_list = self.extract_link_list( response = response )
			if self.debug:
				self.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, url = {response.url}; link_list = {link_list}" )
			else:
				new_url = f"{url_obj.scheme}://{url_obj.netloc}"
				self.log_for_picking_up_the_crawl_break_point(page_type = "index", response = response )
				# 20190806不爬取详情页面了，赶紧先爬取列表页面
				for text_dict in link_list:
					if isinstance( text_dict, dict ) and 0 < len( text_dict ):
						try:
							loader = ItemLoader( item = Gzzfcj1Item(), response = response )
							loader = self.load_items_into_loader( loader = loader, text = text_dict, url = response.url )
							yield loader.load_item()
						except Exception as ex:
							self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, fail to load item. Exception = {ex}" )
				
				# crawling vertically
				# meta_dict = {
				# 	"page_type": "detailed",
				# 	"total_pages": 1,
				# }
				# if self.use_proxy:
				# 	proxies_dict = self.proxy_ip_pool()
				# 	meta_dict["proxy"] = proxies_dict["http"]

				# for one_link in link_list:
				# 	if 0 != one_link.find('/'): one_link = f"/{one_link}"
				# 	this_i_url = f"{new_url}{one_link}"
				# 	if this_i_url in self.crawled_detailed_url_list:
				# 		self.logger.info( f"previously crawled {this_i_url}" )
				# 	else:
				# 		self.logger.info( f"requesting {this_i_url}" )
				# 		yield scrapy.Request( url = this_i_url, cookies=self.cookie_dict, callback = self.parse_detailed_page, meta = meta_dict, dont_filter = True )

				# crawling horizontally
				# http://zfcj.gz.gov.cn/data/Laho/ProjectSearch.aspx?page=4
				if 1 < total_pages and 1 == page:
					meta_dict = response.meta
					if self.use_proxy:
						proxies_dict = self.proxy_ip_pool()
						meta_dict["proxy"] = proxies_dict["http"]
					for i in range( total_pages - 1 ):
						meta_dict["page"] = i + 2
						this_i_url = f"{self.base_url}?page={i + 2}"
						self.logger.info( f"requesting list page at {this_i_url}" )
						yield scrapy.Request( url = f"{this_i_url}", callback = self.parse_list_page, meta = meta_dict, dont_filter = True ) # cookies=self.cookie_dict, 
			
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
						loader = ItemLoader( item = Gzzfcj1Item(), response = response_for_items )
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
