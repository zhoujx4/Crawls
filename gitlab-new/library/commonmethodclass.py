# -*- coding: utf-8 -*-
import os
import sys
import re
import csv
import json
import xlrd
import time
import random
import datetime
import shutil
import socket
import numpy as np
from importlib import import_module
import requests
from requests.exceptions import RequestException
from collections.abc import Iterable

from selenium.webdriver.chrome.webdriver import WebDriver

class CommonMethodClass(object):
	root_path = None
	today = None

	def __init__(self):
		"""
		这个初始化方法仅仅为了测试用；本类有用的方法都是@classmethod的
		revision 20190810
		"""
		self.root_path = os.getcwd()
		self.today = datetime.datetime.now().strftime("%Y%m%d")

	def test(self):
		excel_file_path = os.path.join( self.root_path, "..", "house163", "163data20190810_801.xls" )
		log_file_path = os.path.join( self.root_path, "..", "house163", "logs", f"house163_{self.today}.log" )
		excel_wordbook_dict = CommonMethodClass.read_excel_file( excel_file_path = excel_file_path, log_file_path = log_file_path )
		print( excel_wordbook_dict )

	@classmethod
	def cleanup_webdriver(cls, webdriver = None):
		try:
			webdriver.quit()
			webdriver.close()
		except Exception:
			pass

	@classmethod
	def get_headers(cls, browser = "", cookies = None, referer = None):
		"""
		browser shall ONLY be in ["ChromePC", "Chrome",]
		revision 20190810
		"""
		headers = {
			"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
			"Referer": "http://api.map.baidu.com/lbsapi/getpoint/index.html",
			"X-Requested-With": "XMLHttpRequest",
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
			"Accept-Encoding": "gzip, deflate",
			"Accept-Language": "en-US,en;q=0.9",
			"Cache-Control": "max-age=0",
		}
		if cookies is not None: headers["Cookie"] = cookies
		if referer is not None: headers["Referer"] = referer
		if "ChromePC" == browser: headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"

		return headers

	@classmethod
	def load_item_and_write_csv(cls, info_list = [], url = "", city = "", csv_file_path_str = "", log_file_path = "" ):
		for one_dict in info_list:
			one_dict["city"] = city
			one_dict["url"] = url
			one_dict["server"] = socket.gethostname()
			one_dict["date"] = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
			CommonMethodClass.append_row( key_list = one_dict.keys(), item_list = one_dict.values(), csv_file_path_str = csv_file_path_str, log_file_path = log_file_path )
		return True

	@classmethod
	def append_row(cls, key_list = [], item_list = [], csv_file_path_str = "", log_file_path = "" ):
		try:
			new_file = False if os.path.isfile( csv_file_path_str ) else True
			with open( csv_file_path_str, "a", encoding="utf-8", newline="") as f:
				writer = csv.writer(f)
				if new_file: writer.writerow( key_list )
				writer.writerow( item_list )
		except Exception as ex:
			error_msg = f"cannot write into file {csv_file_path_str}; content is: {item_list}; Exception = {ex}"
			content = f" [Error] Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, {error_msg}"
			CommonMethodClass.write_log( content = content, log_file_path = log_file_path  )
			return False
		else:
			return True

	@classmethod
	def get_file_info( cls, file_dir = "", to_dir = "", log_file_path = "", endswith = ".xls" ):
		"""
		在下载之前file_dir文件夹应该保持空；发现文件已经下载，则将文件移动到to_dir内
		revision 20190810
		"""
		latest_file_path = ""
		latest_file_name = ""
		latest_create_ts = 0.0
		fsize = 0

		moved = False

		if not os.path.isdir(file_dir) or not os.path.isdir(to_dir):
			return (latest_file_path, latest_file_name, latest_create_ts, fsize)

		file_list = os.listdir( file_dir )
		try:
			if 1 < len( file_list ):
				error_msg = f"{file_dir} has more than 1 file ({file_list})"
				content = f" [Error] Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, {error_msg}"
				CommonMethodClass.write_log( content = content, log_file_path = log_file_path  )
				for file in file_list:
					if not file.endswith(endswith):
						continue
					file_path = os.path.join( file_dir, file )
					create_timestamp = os.path.getctime(file_path)
					if latest_create_ts < create_timestamp:
						latest_create_ts = create_timestamp
						latest_file_name = file
					dst_path = os.path.join( to_dir, file )
					shutil.move(file_path, dst_path)
					moved = True
			elif 1 == len(file_list) and file_list[0].endswith(endswith):
				file = file_list[0]
				file_path = os.path.join( file_dir, file )
				latest_create_ts = os.path.getctime(file_path)
				latest_file_name = file
				dst_path = os.path.join( to_dir, file )
				shutil.move(file_path, dst_path)
				moved = True
		except Exception as ex:
			error_msg = f"fail to move file {file_path}, Exception = {ex}"
			content = f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, {error_msg}"
			CommonMethodClass.write_log( content = content, log_file_path = log_file_path  )
		
		if moved:
			latest_file_path = os.path.join( to_dir, latest_file_name )
			fsize = os.path.getsize(latest_file_path)
		
		return (latest_file_path, latest_file_name, latest_create_ts, fsize)

	@classmethod
	def get_element(cls, webdriver = None, xpath = "", elements_bool = False, use_id = False, debug = True, log_file_path = "" ):
		"""
		webdriver could be WebElement
		revision 20190809
		"""
		element = None
		if type(webdriver) not in [WebDriver] or type(xpath) not in [str] or 1 > len(xpath):
			return element
		try:
			if use_id:
				element = webdriver.find_element_by_id( xpath )
			elif elements_bool:
				element = webdriver.find_elements_by_xpath( xpath )
			else:
				element = webdriver.find_element_by_xpath( xpath )
		except NoSuchElementException as ex:
			if debug:
				print( f"{xpath}: NoSuchElementException = {ex}" )
			return None
		except Exception as ex:
			error_msg = f"fail to get element from {webdriver}, Exception = {ex}"
			content = f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, {error_msg}"
			CommonMethodClass.write_log( content = content, log_file_path = log_file_path  )
			return None
		
		return element

	@classmethod
	def write_log(cls, content = None, log_file_path = "", content_only = False):
		"""
		return 1: content has been logged
		return 0: fail to write log file, could be wrong parameter log_file_path
		return -1: wrong parameter content
		revision 20190810
		"""
		log_dir = os.path.dirname(log_file_path)
		if type( log_file_path ) not in [str] or not os.path.isdir( log_dir ):
			log_dir = os.path.join( os.getcwd(), "logs" )
			if not os.path.isdir( log_dir ): log_dir = os.getcwd()
			today = datetime.datetime.now().strftime("%Y%m%d")
			log_file_path = os.path.join( log_dir, f"log_file_{today}.log" )

		if isinstance(content, Iterable) and 0 < len( content ):
			try:
				with open( log_file_path, "a", encoding = "utf-8" ) as log_file:
					if content_only:
						info = f"{content}\n"
					else:
						info = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] {content}\n"
					log_file.write(info)
				return 1
			except Exception as ex:
				print( f"fail to write content ({content}) to log file ({log_file_path}). Exception = {ex}" )
				return 0
		return -1

	@classmethod
	def read_excel_file( cls, excel_file_path = "", log_file_path = "" ):
		"""
		revision 20190810
		references:
			https://www.cnblogs.com/fuqia/p/8989712.html
		"""
		excel_wordbook_dict = {}
		try:
			workbook = xlrd.open_workbook(excel_file_path)
			worksheet_list = workbook.sheets()
			for worksheet in worksheet_list:
				row_num = worksheet.nrows
				col_num = worksheet.ncols
				name = worksheet.name if 0 < len( worksheet.name ) else f"unknown_worksheet_{random.randint(10000,99999)}"
				row_list = []
				for i in range( row_num ):
					this_row_list = []
					for j in range( col_num ):
						this_row_list.append( worksheet.cell_value( i,j ) )
					row_list.append( this_row_list )
				excel_wordbook_dict[name] = row_list
			return excel_wordbook_dict
		except Exception as ex:
			error_msg = f"cannot read excel file {excel_file_path}; Exception = {ex}"
			CommonMethodClass.write_log( content = f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, {error_msg}", log_file_path = log_file_path )

class OtherMethodClass(object):
	"""
	all method to be modified and then moved to CommonMethodClass
	"""
	@classmethod
	def initialize_kafka( cls, kafka_producer = None, kafka_servers = [], spider_obj = None ):
		try:
			if kafka_producer is None:
				from kafka import KafkaProducer # for importing data into hdfs using Kafka
				kafka_producer = KafkaProducer( bootstrap_servers = kafka_servers )
			return kafka_producer
		except Exception as ex:
			errorMsg = f"KafkaProducer module error or fail to import KafkaProducer. Exception = {ex}"
			spider_obj.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, {errorMsg}" )
			return None

	@classmethod
	def log_close_spider( cls, spider_obj = None ):
		if hasattr( spider_obj, "logger" ) and hasattr( spider_obj.logger, "info" ):
			now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
			spider_obj.logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, spider closes at {now}" )

	@classmethod
	def pipeline_to_kafka( cls, spider_obj = None, key_list = [], item_list = [], kafka_topic_str = "", kafka_producer_obj = None ):
		spider_logger_error_ok = False
		if hasattr( spider_obj, "logger" ) and hasattr( spider_obj.logger, "error" ):
			spider_logger_error_ok = True
		
		if not isinstance( kafka_topic_str, str ) or 1 > len( kafka_topic_str ):
			if spider_logger_error_ok:
				spider_obj.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, wrong {kafka_topic_str} (mostly spider.name)" )
			return False
		if not isinstance( key_list, list ) or not isinstance( item_list, list ) or 1 > len( key_list ) or 1 > len( item_list ):
			if spider_logger_error_ok:
				spider_obj.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, empty keys or empty values ({key_list} or {item_list})" )
			return False
		if kafka_producer_obj is None or not hasattr( kafka_producer_obj, "send"):
			if spider_logger_error_ok:
				spider_obj.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, kafka_producer_obj has no send() method" )
			return False

		kafka_producer_obj.send( kafka_topic_str, bytes( json.dumps( dict(zip( key_list, item_list )) ), encoding="utf-8" ), timestamp_ms = int(time.time()*1000) )
		return True

	@classmethod
	def append_row(cls, spider_obj = None, key_list = [], item_list = [], csv_file_path_str = "" ):
		spider_logger_error_ok = False
		if hasattr( spider_obj, "logger" ) and hasattr( spider_obj.logger, "error" ):
			spider_logger_error_ok = True
		try:
			if not isinstance( csv_file_path_str, str ) or 1 > len( csv_file_path_str ):
				if spider_logger_error_ok:
					spider_obj.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, missing csv filename or CRAWLED_DIR setting" )
			else:
				new_file = False
				if not os.path.isfile( csv_file_path_str ):
					new_file = True
				with open( csv_file_path_str, "a", encoding="utf-8", newline="") as f:
					writer = csv.writer(f)
					if new_file:
						writer.writerow( key_list )
					writer.writerow( item_list )
		except Exception as ex:
			if spider_logger_error_ok:
				spider_obj.logger.error( f"cannot write into file {csv_file_path_str}; content is: {item_list}; Exception = {ex}" )
			return False
		else:
			return True

	@classmethod
	def extract_items_and_keys_from_content(cls, raw_key_list=[], raw_item_list = [], content_field_name_str = "content"):
		result_bool = False
		key_list = []
		item_list = []

		index = -1
		content_dict = {}
		if content_field_name_str in raw_key_list:
			index = raw_key_list.index( content_field_name_str )
			if -1 < index and index < len( raw_item_list ):
				content_dict = eval(raw_item_list[index])
				raw_item_list.remove( raw_item_list[index] )
				raw_key_list.remove( content_field_name_str )

				keys = []
				items = []
				for key, value in content_dict.items():
					keys.append( key )
					items.append( value )
				key_list = keys + raw_key_list
				item_list = items + raw_item_list
				result_bool = True
		return (result_bool, key_list, item_list)

	@classmethod
	def get_items_and_keys(cls, item=None, excluded_key_list=[]):
		item_list = []
		key_list = []
		if item is None:
			return (key_list, item_list)
		for index, key in enumerate( item ):
			if key not in excluded_key_list:
				key_list.append( key )
				if not isinstance( item[key], Iterable):
					item_list.append( item[key] )
				if 0 == len(item[key]):
					item_list.append("") # type has been changed from Iterable to str
				elif 1 == len(item[key]):
					item_list.append( item[key][0] )
				else:
					item_list.append( item[key] )
		return (key_list, item_list)

	@classmethod
	def parse_gaode_json(cls, json_text = ""):
		return_dict = {
			"count": 0,
			"longitude": np.nan,
			"latitude": np.nan,
			"adcode": np.nan,
		}
		if 1 > len( json_text ):
			return return_dict
		json_obj = json.loads( json_text )
		if json_obj is not None and "count" in json_obj.keys() and 0 < int( json_obj["count"] ):
			if "geocodes" in json_obj.keys() and isinstance(json_obj["geocodes"], list) and 0 < len( json_obj['geocodes'] ):
				adcode = json_obj['geocodes'][0]['adcode']
				temp = json_obj['geocodes'][0]['location']
				temp_list = temp.split(',')
				if 1 < len( temp_list ):
					longitude = temp_list[0]
					latitude = temp_list[1]
					return_dict['longitude'] = longitude
					return_dict['latitude'] = latitude
					return_dict['adcode'] = adcode
					return_dict["count"] = 1
		return return_dict

	@classmethod
	def clean_addr(cls, text):
		"""
		return string before (, *, or （
		"""
		if isinstance(text, str):
			text = text.strip('*')
			if -1 < text.find('（'):
				temp = text.split('（')
				if 0 < len( temp ):
					text = temp[0]
			if -1 < text.find('('):
				temp = text.split('(')
				if 0 < len( temp ):
					text = temp[0]
			if -1 < text.find('*'):
				temp = text.split('*')
				if 0 < len( temp ):
					text = temp[0]
		return text

class CommonClass(object):
	def __init__(self):
		pass

	@classmethod
	def safely_convert_to_int( cls, to_int_obj = None, spider_obj = None, convert_strategy = "match_all_digits" ):
		"""
		convert_strategy:
			"match_all_digits": "12af79aalf045" will return int(1279045); "" will return 0
			"only_first_part": "12af79aalf045" will return int(12); "" will return 0
			"strict": "12af79aalf045" will return None; "" will return None
		"""
		try:
			if isinstance( to_int_obj, (int, float, bool) ):
				return int( to_int_obj )
			elif isinstance( to_int_obj, str ):
				pattern = re.compile(r'\d+')
				digits = pattern.findall( to_int_obj )
				if isinstance( digits, list ) and 0 < len(digits):
					if "match_all_digits" == convert_strategy:
						return int( "".join( digits ) )
					elif "only_first_part" == convert_strategy:
						return int( digits[0] )
					elif "strict" == convert_strategy:
						errorMsg = f"strict strategy is used but {to_int_obj} has chars other than digits"
						spider_obj.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, {errorMsg}" )
						return None
					else:
						return int( "".join( digits ) )
				elif isinstance( digits, list ):
					if "strict" == convert_strategy:
						errorMsg = f"strict strategy is used but {to_int_obj} is an empty str"
						spider_obj.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, {errorMsg}" )
						return None
					elif convert_strategy in ["match_all_digits", "only_first_part", ]:
						return 0
					errorMsg = f"wrong parameter (convert_strategy)"
					spider_obj.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, {errorMsg}" )
					return None
		except Exception as ex:
			errorMsg = f"{to_int_obj} (type == {type(to_int_obj)}) cannot be converted to int. Exception = {ex}"
			spider_obj.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, {errorMsg}" )
			return None
		errorMsg = f"unknow error!"
		spider_obj.logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, {errorMsg}" )
		return None

	@classmethod
	def get_custom_settings_dict(cls, spider = 'no_spider_name'):
		current_path = os.getcwd()
		temp = current_path.split('\\')
		project_name = str( temp[len(temp) - 1] ) if 0 < len(temp) else "no_project_name"
		settings_dict = {}
		try:
			module = import_module( f"{spider}.settings_{spider}" ) # f"{project_name}.settings_{spider}"
			for key in dir(module):
				if key.isupper():
					settings_dict[ key ] = getattr(module, key)
		except Exception as ex:
			print( f"Error happened while getting custom_settings. Exception = {ex}" )
		return settings_dict

	@classmethod
	def clean_string(cls, string = "", char_to_remove = ['\r', '\n', '\t', ' ',]):
		if string is None or 1 > len( string ) or char_to_remove is None or 1 > len(char_to_remove):
			return ""
		for char in char_to_remove:
			if '"' == char:
				string = string.strip( '"' )
			else:
				string = string.replace(char, '')
		return string

	@classmethod
	def replace_string(cls, string = "", char_to_remove = ['\r', '\n', '\t', ' ',], new_char = '' ):
		if string is None or 1 > len( string ) or char_to_remove is None or 1 > len(char_to_remove):
			return ""
		for char in char_to_remove:
			string = string.replace(char, new_char)
		return string

	@classmethod
	def only_this_char_in_string(cls, string = "", char = '' ):
		if 1 > len( char ):
			return True
		if 1 > len( string ):
			return False
		temp = string.strip( char )
		return True if 0 == len( temp ) else False

	@classmethod
	def find_digits_from_str( cls, string="", return_all = False ):
		"""
			return_all == False: "123abc389" will ONLY return "123"
			return_all == True: returns ["123", "389",]
		"""
		pattern = re.compile(r'\d+')
		digits = pattern.findall( string )
		if isinstance( digits, list ) and 0 < len(digits) and not return_all:
			return digits[0]
		elif not return_all:
			return ""
		return digits

	@classmethod
	def check_file_downloaded(cls, filename = "", dir_path = "" ):
		if -1 == filename.find("*") and -1 == filename.find("?"):
			return os.path.isfile( os.path.join( dir_path, filename ) )

	@classmethod
	def write_one_row(cls, item_list=[], file_path = "", all_keys=[], no_json_dumps=False, spider=None):
		has_no_file = False
		if not os.path.isfile( file_path ):
			has_no_file = True
		try:
			with open( file_path, 'a', encoding='utf-8', newline="") as f:
				writer = csv.writer(f)
				if has_no_file:
					writer.writerow( all_keys ) # item.keys()
				if no_json_dumps:
					writer.writerow( item_list )
				else:
					# temp = json.dumps(item_list, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, cls=None, indent=None, separators=None, encoding="utf-8", default=None, sort_keys=False, **kw)
					temp = []
					for one_item in item_list:
						temp.append( json.dumps([one_item], allow_nan=True) )
					writer.writerow( temp )
		except Exception as ex:
			spider.logger.error( f"cannot write csv file in Method write_one_row of Class DianpingPipeline. Exception = {ex}; item_list = {item_list}; all_keys = {all_keys} " )

	@classmethod
	def get_latest_time(cls, file_name = "", folder = "", logger = None):
		try:
			this_path = os.path.join( folder, file_name )
			access_time = os.path.getatime( this_path ) # access_time = 1553139157.6529193; type = <class 'float'>
			create_time = os.path.getctime( this_path )
			modify_time = os.path.getmtime( this_path )
			# return min( [access_time, create_time, modify_time, ] )
			return max( [access_time, create_time, modify_time, ] )
		except Exception as ex:
			logger.error( f"cannot get file time of {file_name} in {folder}. Exception = {ex} " )
		return -1

	@classmethod
	def remove_0_len_element(cls, list4remove = []):
		return_list  = []
		for one in list4remove:
			if 0 < len( one ):
				return_list.append( one )
		return return_list

	@classmethod
	def get_latest_file_name(cls, this_dir = "", suffix=".css", logger = None):
		all_files = []
		file_list = os.listdir( this_dir )
		if 0 < len( suffix ):
			for one in file_list:
				if one.endswith( suffix ):
					all_files.append( one )
		else:
			all_files = file_list
		# earliest_time = sys.maxsize
		latest_time = 0
		latest_file = ""
		for one in all_files:
			time_one = CommonClass.get_latest_time(file_name = one, folder= this_dir, logger = logger)
			if latest_time < time_one and -1 < time_one:
				latest_time = time_one
				latest_file = one
		return latest_file

	@classmethod
	def get_cleaned_string_by_splitting_list(cls, string_or_list, char_to_remove = ['\r', '\n', '\t', ' ',]):
		temp_list = []
		return_str = ""
		if isinstance(string_or_list, str):
			temp_list = string_or_list.split("\n")
		elif isinstance( string_or_list, list):
			temp_list = string_or_list
		if 0 < len( temp_list ):
			new_list = []
			for one in temp_list:
				temp = CommonClass.clean_string( string = one, char_to_remove = ['\r', '\n', '\t', ' ',] )
				if isinstance(temp, str) and 0 < len( temp ):
					new_list.append( temp )
			if 0 < len( new_list ):
				return_str = "; ".join( new_list )
		return return_str

	@classmethod
	def get_show_ip_url(self):
		url = "https://www.coursehelper.site/index/index/getHeaders"
		now = int(time.time())
		token = f"Guangzhou{str(now)}"
		m = hashlib.md5()  
		m.update( token.encode(encoding = 'utf-8') )
		return f"{url}/token/{m.hexdigest()}"

	@classmethod
	def get_proxies( cls, proxy_dict = {} ):
		"""get_proxies() Method generates the proxies for requests
		"""
		if proxy_dict is None or not isinstance( proxy_dict, dict ) or 1 > len( proxy_dict ):
			# Account Name and password of Dragonfly IP Agency;
			proxy_dict = {
				"proxy_pwd": "00rPeu7HKvmu",
				"proxy_user": "JEVJ1625573267906612",
				"proxy_host": "dyn.horocn.com",
				"proxy_port": "50000",
			}

		proxy_meta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
			"host": proxy_dict["proxy_host"],
			"port": proxy_dict["proxy_port"],
			"user": proxy_dict["proxy_user"],
			"pass": proxy_dict["proxy_pwd"],
		}

		return {
			"http": proxy_meta,
			"https": proxy_meta,
		}

	@classmethod
	def dragonfly(cls, target_url = '', params={}, headers = {}, cookies={}, method="get", proxy_dict = {} ):
		"""dragonfly method accepts:
		target_url = '', params={}, headers = {}, cookies={} will be used for requests.post() or get() like this:
		requests.get(target_url, params=params, headers=headers, cookies=cookies, proxies=proxies)
		method: string, could only be "get" or "post"
		proxy_dict: dict, shall include these keys: proxy_pwd, proxy_user, proxy_host, proxy_port; if empty dict is passed in, default values will be used

		returns code (int), a string (str):
		-1, f"wrong parameters. target_url = {target_url}"
		-1, f"method shall only be get or post"
		-2, f"Exception happens while crawling {target_url} Exception = {ex}"
		int(response.status_code), response.text
		int(response.status_code), f"No response.text is returned. "
		0, f"Unknown error from server. no response.status_code! "
		-3, f"need next proxy."
		"""
			
		response = ""
		if 1 > len(target_url):
			return (-1, f"wrong parameters. target_url = {target_url}")

		if headers is None or not isinstance(headers, dict) or 1 > len(headers):
			headers = {
				"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
				"Referer": "https://www.baidu.com",
			}

		proxies = CommonClass.get_proxies(CommonClass, proxy_dict)

		while True:
			try:
				if "get" == method:
					response = requests.get(target_url, params=params, headers=headers, cookies=cookies, proxies=proxies) # .content.decode()
				elif "post" == method:
					response = requests.post(target_url, params=params, headers=headers, cookies=cookies, proxies=proxies)
				else:
					response = f"method shall only be get or post"
					return (-1, response)
			except RequestException as ex:
				return cls.dragonfly( target_url=target_url, params=params, headers=headers, cookies=cookies, method=method, proxy_dict=proxy_dict )
			except Exception as ex:
				return ( -2, f"Exception happens while crawling {target_url} Exception = {ex}" )
			else:
				if hasattr(response, 'status_code') and hasattr(response, 'text'):
					return ( int(response.status_code), response.text )
				elif hasattr(response, 'status_code'):
					return ( int(response.status_code), f"No response.text is returned." )
				else:
					return (0, f"Unknown error from server. no response.status_code! ")
		return ( -3, f"need next proxy." )

	@classmethod
	def debug_get_first10_from_dict(cls, dict4string = {}, first = 10):
		debug_string = ""
		debug_counter = 0
		for key in dict4string:
			debug_string += f"{key}:{dict4string[key]},"
			debug_counter += 1
			if first < debug_counter:
				break
		return debug_string

if __name__=='__main__':
	app = CommonMethodClass( )
	app.test()
