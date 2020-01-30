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
from cnemc1.items import Cnemc1Item

class Gzzfcj1Spider(scrapy.Spider):
	"""
	20190806王总指出目前还缺少空气质量，本爬虫爬取中国环境监测总局官网的空气质量
	http://www.cnemc.cn/sssj/
		revision 20190806
	"""
	name = "cnemc1"

	root_path = ""
	log_dir = ""
	debug = False
	run_purpose = None
	save_every_response = False
	overwrite_today = ""
	crawled_dir = ""
	saved_json_dir = ""
	base_url = ""

	custom_settings = CommonClass.get_custom_settings_dict(spider=name)

	proxy_ip_dict = {}
	min_proxy_ip_life_time = 6
	max_proxy_ip_life_time = 180
	use_proxy = False
	proxy_agent = ""

	maximal_requests_of_one_crontab_process = 23
	interval_between_requests = 1800
	request_counter = 0
	last_request_time = 0.0
		
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
		self.saved_json_dir = self.settings.get( name = "SAVED_JSON", default="" )
		self.base_url = self.settings.get( name = "BASE_URL", default="" )

		if 1 > len( self.crawled_dir ) or 1 > len( self.saved_json_dir ):
			error_msg = f"missing CRAWLED_DIR ({self.crawled_dir}), SAVED_JSON ({self.saved_json_dir}) setting(s)"
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
		if not os.path.isdir( self.saved_json_dir ):
			os.makedirs( self.saved_json_dir )

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

	def start_requests(self):
		self.init_self_attributes()
		self.make_dirs()

		if "READ_HTML" == self.run_purpose: # READ_HTML is one kind of debug
			url = 'http://quotes.toscrape.com/page/1/'
			yield scrapy.Request( url = url, callback = self.read_and_parse )
		elif "PRODUCTION_RUN" == self.run_purpose:
			urls = [
				# "http://www.cnemc.cn/sssj/", # 中国环境监测总局，实时数据页面
				self.base_url,
			]
			meta_dict = {}
			if self.use_proxy:
				proxies_dict = self.proxy_ip_pool()
				if 1 > len( proxies_dict):
					sys.exit(3)
				meta_dict["proxy"] = proxies_dict["http"]
			
			formdata_dict = {} # 没有任何表单字段需要post给目标网站
			for url in urls:
				# yield scrapy.RequestForm( url = url, callback = self.parse_json, meta = meta_dict, dont_filter = True )
				# yield scrapy.Request( url = url, callback = self.parse_list_page, meta = meta_dict, dont_filter = True )
				self.last_request_time = time.time()
				yield scrapy.FormRequest( url = url, formdata = formdata_dict, callback = self.parse_json, meta = meta_dict, dont_filter = True )
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

	def save_json(self, response=None ):
		json_dict = {}
		if response is None or not hasattr(response, "body") or not hasattr( response, "url" ) or not hasattr( response, "meta"):
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, bad response object" )
			return json_dict

		now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		try:
			json_dict = json.loads( response.body )
			file_path = os.path.join( self.saved_json_dir, f"cnemc_sssj_{now}.json" )
			with open( file_path, "wb" ) as f:
				f.write( response.body )
		except Exception as ex:
			error_msg = f"failed to write response.body from {response.url}; Exception = {ex}"
			self.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		
		temp_dict = {}
		abandoned_key_list = ["localCityAir", "airDataTotal", "waterRealTimeList", "waterWeekList", "waterDataTotal", ]
		for index, key in enumerate( json_dict ):
			if key in abandoned_key_list:
				continue
			temp_dict[key] = json_dict[key]
		temp_dict["response_time"] = now
		return temp_dict

	def parse_json(self, response = None):
		"""
		经过测试，没有发现请求http://www.cnemc.cn/getIndexData.do需要cookie
		可以直接在start_requests方法内请求这个
		print( dir(response) )
		[
		'_DEFAULT_ENCODING', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', 
		'__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', 
		'__setattr__', '__sizeof__', '__slots__', '__str__', '__subclasshook__', '__weakref__', 
		'_auto_detect_fun', '_body', '_body_declared_encoding', '_body_inferred_encoding', '_cached_benc', '_cached_selector', '_cached_ubody', 
		'_declared_encoding', '_encoding', '_get_body', '_get_url', '_headers_encoding', '_set_body', '_set_url', '_url', 
		'body', 'body_as_unicode', 'copy', 'css', 'encoding', 'flags', 'follow', 'headers', 'meta', 'replace', 'request', 'selector', 'status', 'text', 'url', 'urljoin', 'xpath'
		]
		print( dir(response.request) )
		[
		'__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', 
		'__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', 
		'__slots__', '__str__', '__subclasshook__', '__weakref__', 
		'_body', '_encoding', '_get_body', '_get_url', '_meta', '_set_body', '_set_url', '_url', 
		'body', 'callback', 'cookies', 'copy', 'dont_filter', 'encoding', 'errback', 'flags', 'headers', 'meta', 'method', 'priority', 'replace', 'url'
		]
		"""
		url_obj = parse.urlparse( response.url )
		has_url_error = self.url_contains_error( url_obj_path = url_obj.path )
		if has_url_error:
			return False

		json_dict = self.save_json( response = response )
		if isinstance( json_dict, dict ) and 0 < len( json_dict ):
			loader = ItemLoader( item = Cnemc1Item(), response = response )
			loader = self.load_items_into_loader( loader = loader, text = json_dict, url = response.url )
			yield loader.load_item()

		# get data again after 30 minutes
		if self.request_counter < self.maximal_requests_of_one_crontab_process:
			while( self.check_time_interval() ):
				time.sleep(10)
			
			self.request_counter += 1
			self.last_request_time = time.time()
			now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
			self.logger.info( f" requesting cnemc sssj at {now} ( {self.request_counter} of { self.maximal_requests_of_one_crontab_process } )")
			meta_dict = {}
			if self.use_proxy:
				proxies_dict = self.proxy_ip_pool()
				if 1 > len( proxies_dict):
					sys.exit(3)
				meta_dict["proxy"] = proxies_dict["http"]
			
			formdata_dict = {} # 没有任何表单字段需要post给目标网站
			yield scrapy.FormRequest( url = self.base_url, formdata = formdata_dict, callback = self.parse_json, meta = meta_dict, dont_filter = True )

	def check_time_interval( self ):
		if not isinstance( self.last_request_time, float ):
			return False
		if time.time() - self.last_request_time > float(self.interval_between_requests):
			return False
		return True
			
	def read_and_parse(self, response = None):
		file_list = os.listdir( self.saved_json_dir )
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
				html_file_path = os.path.join( self.saved_json_dir, one_file )
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
						loader = ItemLoader( item = Cnemc1Item(), response = response_for_items )
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
