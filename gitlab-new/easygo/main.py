#! /usr/local/bin/python3
# coding: utf-8
# __author__ = "lsg" # https://zhuanlan.zhihu.com/p/30772570
# __date__ = 2017/10/16 16:11

#加载内置包
import requests
from requests.exceptions import RequestException
import json
import time
import datetime
import sys
import os
import csv
import random
import pandas

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

from easygo import qqlist
from easygo import settings
from easygo import transCoordinateSystem
from easygo.dragonfly import Dragonfly

class CookieException(Exception):
	def __init__(self):
		Exception.__init__(self)

class easygospider(object):
	def get_city_chinese_name(self, city = ""):
		default_city = "岳阳"
		if city is None or 1 > len( city ):
			return default_city
		city_chinese_name_list = settings.city_chinese_name_list if hasattr(settings, "city_chinese_name_list") else {}
		if 1 > len( city_chinese_name_list ):
			return default_city
		city_key = city
		if -1 < city.find("_"):
			temp_list = city.split("_")
			city_key = temp_list[0]
		if city_key not in city_chinese_name_list.keys():
			return default_city
		return city_chinese_name_list[city_key]

	def __init__(self, request_counter = 0, cookies = None):
		self.rootpath = settings.rootpath if hasattr(settings, "rootpath") else None
		self.input = settings.xy_name if hasattr(settings, "xy_name") else None # file name to input lng and lat data
		self.finished_input = None
		self.city = settings.city if hasattr(settings, "city") else None
		self.city_chinese_name = self.get_city_chinese_name( self.city )
		self.logfilepath = settings.logfilepath if hasattr(settings, "logfilepath") else None # file path to save log files
		self.library_path = settings.library_path if hasattr(settings, "library_path") else None
		self.input_path = settings.input_path if hasattr(settings, "input_path") else None
		self.filename = settings.filename_prefix if hasattr(settings, "filename_prefix") else None # the prefix part of the result file name
		self.max_proxies = settings.max_proxies if hasattr(settings, "max_proxies") else 20
		self.proxy_pwd = settings.proxy_pwd if hasattr(settings, "proxy_pwd") else None
		self.proxy_user = settings.proxy_user if hasattr(settings, "proxy_user") else None
		self.get_cookies_method = settings.get_cookies_method if hasattr(settings, "get_cookies_method") else 2
		self.cookies = cookies
		self.sleeptime_between_cookies = settings.sleeptime_between_cookies if hasattr(settings, "sleeptime_between_cookies") else 120
		self.browser = settings.browser if hasattr(settings, "browser") else 'Chrome' # can only be in [ 'FireFox', 'IE', 'Chrome']
		self.use_proxy = settings.use_proxy if hasattr(settings, "use_proxy") else True
		self.delay_time = settings.delay_time if hasattr(settings, "delay_time") else 5 # 5 seconds
		self.minimal_delay = settings.minimal_delay if hasattr(settings, "minimal_delay") else 0.1
		self.debug = settings.debug if hasattr(settings, "debug") else False
		self.qq_number_list = qqlist.qq_list
		self.save_every_response = settings.save_every_response if hasattr(settings, "save_every_response") else False

		self.finished_check_zero_log = None
		self.need_update_center = False
		self.center = []
		self.repeat_request_times_upon_empty_data = settings.repeat_request_times_upon_empty_data if hasattr(settings, "repeat_request_times_upon_empty_data") else 3
		self.threshold_to_turn1 = settings.threshold_to_turn1 if hasattr(settings, "threshold_to_turn1") else 50
		self.request_counter = request_counter
		self.high_population_densitiy = settings.high_population_densitiy if hasattr(settings, "high_population_densitiy") else False

	def get_headers(self):
		if 'IE' == self.browser:
			return {
				"User-Agent": "Mozilla/5.0 (Windows Phone 10.0; Android 6.0.1; Microsoft; Lumia 950) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Mobile Safari/537.36 Edge/15.15063",
				"Referer": "http://c.easygo.qq.com/eg_toc/map.html?origin=",
				"X-Requested-With": "XMLHttpRequest",
				"Accept": "application/json",
				"Accept-Encoding": "gzip, deflate",
				"Accept-Language": "zh-CN",
			}
		elif 'Chrome' == self.browser:
			return {
				"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
				"Referer": "http://c.easygo.qq.com/eg_toc/map.html?origin=",
				"X-Requested-With": "XMLHttpRequest",
				"Accept": "application/json",
				"Accept-Encoding": "gzip, deflate",
				"Accept-Language": "en-US,en;q=0.9",
			}
		elif "FireFox" == self.browser:
			return {
				"Accept-Encoding": "gzip, deflate",
				"Accept-Language": "zh-CN,zh;q=0.9",
				"Referer": "http://c.easygo.qq.com/eg_toc/map.html?origin=",
				"User-Agent": "Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1",
			}
		elif "Opera" == self.browser:
			return {
				"Accept-Encoding": "gzip, deflate",
				"Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
				"Referer": "http://c.easygo.qq.com/eg_toc/map.html?origin=csfw",
				"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
			}
		elif "360" == self.browser:
			return {
				"Accept-Encoding": "gzip, deflate",
				"Accept-Language": "zh-CN,zh;q=0.9",
				"Referer": "http://c.easygo.qq.com/eg_toc/map.html?origin=csfw",
				"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1",
			}
		else:
			return {}
				
	def get_input_list(self, pickup_last = True):
		"""
		return a list []
		"""
		center = []
		requested = []
		temp_list = []
		today = datetime.datetime.now().strftime("%Y%m%d")
		try:
			with open( os.path.join( self.input_path, self.input ), 'r', encoding='utf-8') as f:
				for item in f.readlines()[1:]:
					center.append(tuple(item.strip().split(",")[-5:]))
				if self.finished_input is None:
					self.finished_input = f"{self.input}{today}.log"
				finished_file_path = os.path.join( self.logfilepath, self.finished_input )
				if pickup_last and os.path.isfile( finished_file_path ):
					with open( finished_file_path, 'r', encoding='utf-8') as log_file:
						requested = []
						for item in log_file.readlines():
							value = item.strip().split(",")
							requested.append( f"{value[0]}___{value[1]}" )
					if 0 < len( requested ):
						for value in center:
							key = f"{value[0]}___{value[1]}"
							if key not in requested:
								temp_list.append( value )
						center = temp_list
				# we need to write back to center file and therefore do not shuffle here
		except Exception as ex:
			center = []
			self.write_log( f"cannot read xy_list file ({os.path.join( self.input_path, self.input )}). Exception = {ex}" )
		if len(requested) < len( temp_list) or 0 < len(center):
			self.center = center
			return center
		else:
			print( f"There are already {len(requested)} requests; Number of points waiting for requesting = {len(center)}" )
			sys.exit(3)

	# 初始化用于爬虫的网格，形成url
	def initial_paramslist(self, pickup_last = True):
		center = self.get_input_list( pickup_last = pickup_last )
		print( f"there are {len(center)} requests ahead." )

		#生成四至范围（按照2.6km范围生成，防止有遗漏点，如有重复，最后去重的时候处理）
		# 这样做就可以使用lng_delta = 0.01167*edge得到近似5公里的经度最大和最小值
		square_list = []
		for item in center:
			lng, lat, ok0, max_value, max_timestamp = item
			lng, lat = float(lng), float(lat)
			square_list.append([
				lng - 0.5 * settings.lng_delta,
				lng + 0.5 * settings.lng_delta,
				lat - 0.5 * settings.lat_delta,
				lat + 0.5 * settings.lat_delta,
			])
		#生成待抓取的params
		paramslist = []
		for item in square_list:
			lng_min, lng_max, lat_min, lat_max = item
			# lng_min, lat_min = transCoordinateSystem.wgs84_to_gcj02(lng_min, lat_min)
			# lng_max, lat_max = transCoordinateSystem.wgs84_to_gcj02(lng_max, lat_max)
			# 20190403 Peter changes these to the following 2 lines after talking with Zeng Ji.
			lng_min, lat_min = transCoordinateSystem.bd09_to_gcj02(lng_min, lat_min)
			lng_max, lat_max = transCoordinateSystem.bd09_to_gcj02(lng_max, lat_max)
			params = {
				"lng_min": lng_min,
				"lat_max": lat_max,
				"lng_max": lng_max,
				"lat_min": lat_min,
				"level": 16,
				"city": self.city_chinese_name,
				"lat": "undefined",
				"lng": "undefined",
				"_token": ""
			}
			paramslist.append(params)
			# http://c.easygo.qq.com/api/egc/heatmapdata?lng_min=113.37325&lat_max=22.94144&lng_max=113.39523&lat_min=22.93400&level=16&city=%E5%B9%BF%E5%B7%9E&lat=undefined&lng=undefined&_token=
		# if self.debug:
		# 	self.write_parameters( center, paramslist )
		self.write_parameters( center, paramslist )
		return (center, paramslist)

	def write_parameters( self, center=[], paramslist=[] ):
		now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		if paramslist is not None and 0 < len( paramslist ):
			logfilename = f"{self.city}_request_parameters{now}.log"
			self.write_log( str(json.dumps(paramslist)), logfilename = logfilename, content_only = True )
		if center is not None and 0 < len( center ):
			logfilename = f"{self.city}_request_centers{now}.log"
			self.write_log( str(json.dumps(center)), logfilename = logfilename, content_only = True )

	def input_cookies(self):
		if self.cookies is None or 1 > len( self.cookies ):
			cookies_string = input("please input cookies:")
		by_hand_list = cookies_string.split(';')
		all_by_hand = {}
		for one in by_hand_list:
			temp = one.strip()
			temp_list = temp.split('=')
			all_by_hand[ temp_list[0] ] = temp_list[1]
		self.cookies = all_by_hand
		return all_by_hand

	def read_cookies_pool_file(self):
		returned_dict = {}
		cookies_pool_file = "internal_cookies_pool.txt" # 采用单个文件不加锁方案
		cookies_list = []
		try:
			with open( os.path.join( self.input_path, cookies_pool_file ), 'r', encoding='utf-8') as f:
				for item in f.readlines():
					cookies_list.append( item )
		except Exception as ex:
			return returned_dict
		if 1 > len( cookies_list ):
			return returned_dict
		while 0 < len( cookies_list ):
			temp = cookies_list.pop()
			row_list = temp.strip().split(",")
			if 2 > len(row_list) or 1 > len(row_list[0]) or 1 > len( row_list[1] ):
				return returned_dict
			try:
				cookie_pairs = tuple( row_list[1].strip().split(";") )
				for one in cookie_pairs:
					one_list= one.split('=')
					returned_dict[ one_list[0] ] = one_list[1]
				if 1 > len( returned_dict ):
					continue

				# save all other cookies except the popped one
				string = ""
				for item in cookies_list:
					string += f"{item}"
				with open( os.path.join( self.input_path, cookies_pool_file ), 'w', encoding='utf-8') as f:
					f.write(string)
			except Exception as ex:
				return returned_dict
			else:
				self.browser = str(row_list[0])
				self.cookies = returned_dict
				return returned_dict
				
		return returned_dict

	def get_cookie(self):
		if 1 == self.get_cookies_method:
			return self.input_cookies()
		elif 2 == self.get_cookies_method:
			return self.read_cookies_pool_file()
		print( f"self.get_cookies_method = {self.get_cookies_method}; from now on, this value can ONLY be 1 or 2." )
		sys.exit(3)

	def spyder_proxy(self, cookie, params):
		headers = self.get_headers()

		for i in range(0, self.max_proxies, 1):
			# returns 0, 200, -100, -1, -2, -3
			target_url = "http://c.easygo.qq.com/api/egc/heatmapdata"
			code, resp = Dragonfly.dragonfly( target_url = target_url, params = params, cookies = cookie, headers = headers, method="get", return_params=False, proxy_user = self.proxy_user, proxy_pwd = self.proxy_pwd )
			
			if 200 == code:
				return resp
			elif -1 == code or -100 == code:
				self.write_log( f"Dragonfly.dragonfly returns: {resp}" )
				break # wrong parameters or rejected by Wechat Server
			elif 0 == code:
				self.write_log( f"Internet error. response = {resp}" )
				break
			elif -2 == code or -3 == code:
				continue
			else:
				self.write_log( f"failed to write file. response = {resp}" )
		return '' # after trying self.max_proxies times, just return ''

	def get_responsed_json_filename(self, params = {}, timestamp = "1554373116"):
		# {"lng_min": 113.49433231329479, "lat_max": 27.027974692588113, "lng_max": 113.52456714601139, "lat_min": 27.004635152747753, "level": 16, "city": "zhuzhou", "lat": "undefined", "lng": "undefined", "_token": ""}
		keys = ["lng_min", "lat_max", "lng_max", "lat_min", ]
		string = ""
		for one in keys:
			string += f"{one}{params[one]}___"
		# return f"{params['city']}___{string}{timestamp}.json"
		# On 20190430, Peter changed params['city'] to Chinese; so we need to use self.city instead of the city's Chinese name
		return f"{self.city}___{string}{timestamp}.json"

	def save_reponsed_json_file(self, params = {}, response = "" ):
		if 1 > len( params ) or 1 > len( response ):
			return False
		temp_dict = eval( response )
		if 'nt' in temp_dict.keys():
			timestamp = temp_dict["nt"]
		else:
			timestamp = int(time.time())
		filename = self.get_responsed_json_filename(params = params, timestamp = timestamp)
		try:
			with open( os.path.join( self.rootpath, "jsons", filename ),'a',encoding='utf-8') as f:
				f.write(response)
			return True
		except Exception as ex:
			self.write_log( f"Cannot write filename = {filename}; response = {response}" )
			return False

	def spyder(self,cookie,params):
		headers = self.get_headers()
		
		while True:
			try:
				url = "http://c.easygo.qq.com/api/egc/heatmapdata"
				r = requests.get( url, headers=headers, cookies=cookie, params=params )
				if r.status_code == 200:
					temp_dict = eval( r.text )
					if 0 == int(temp_dict["code"]):
						if self.save_every_response:
							self.save_reponsed_json_file(params = params, response = r.text )
						return r.text
					elif -100 == int(temp_dict["code"]):
						self.write_log( f"WeChat server returns -100 in spyder Method. params = {params}" )
						char = input( f"WeChat server returns -100 in spyder Method. params = {params}. enter c to get next cookie")
						if "c" != char:
							sys.exit(-2) # 该用户访问次数过多
						return ""
				else:
					raise CookieException
			except CookieException:
				self.write_log( f"WeChat server returns wrong r.status_code {r.status_code} in spyder Method. params = {params}" )
				char = input( f"WeChat server returns wrong r.status_code {r.status_code} in spyder Method. enter c to get next cookie" )
				if "c" != char:
					sys.exit(-2) # wrong cookie
				return ""
			except Exception as ex:
				self.write_log( f"In spyder Method, WeChat server returns Exception = {ex}" )
				char = input( f"Internet connection lost (check your proxy). try again? enter r to retry or c to get next cookie. Exception = {ex}" )
				if "c" == char:
					return ""
				elif "r" != char:
					sys.exit(-2)

	def record_finished(self, tuple_row):
		if self.finished_input is None:
			self.finished_input = f"{self.input}{datetime.datetime.now().strftime('%Y%m%d')}.log"
		try:
			with open( os.path.join( self.logfilepath, self.finished_input ), "a", encoding="utf-8") as f:
				f.write( f"{str(tuple_row[0])},{str(tuple_row[1])}\n" )
		except Exception as ex:
			self.write_log( f"Exception happended in Method record_finished. Exception = {ex}; center row = {tuple_row}" )

	def check_and_update_center( self, response = None, tuple_row= (), index = 0 ):
		# x,y,ok0,max_value,max_timestamp
		temp_dict = eval( response )
		timestamp = time.time()
		if 'nt' in temp_dict.keys():
			timestamp = temp_dict["nt"]
		data = []
		if 'data' in temp_dict.keys():
			data = temp_dict["data"]
		if int( tuple_row[3] ) < len( data ) and index < len(self.center):
			self.need_update_center = True
			new_row = (tuple_row[0], tuple_row[1], tuple_row[2], str( len( data ) ), str(timestamp) )
			self.center[index] = new_row

	def record_check_zero( self, response = None, tuple_row= () ):
		temp_dict = eval( response )
		timestamp = time.time()
		if 'nt' in temp_dict.keys():
			timestamp = temp_dict["nt"]
		data = []
		if 'data' in temp_dict.keys():
			data = temp_dict["data"]
		temp = self.input
		today = datetime.datetime.now().strftime('%Y%m%d')
		if self.finished_check_zero_log is None:
			self.finished_check_zero_log = temp.replace( ".txt", f"{today}check0.log" )
		record0filename = temp.replace( ".txt", f"{today}log0.log" )
		try:
			with open( os.path.join( self.logfilepath, self.finished_check_zero_log ), "a", encoding="utf-8") as f:
				f.write( f"{str(tuple_row[0])},{str(tuple_row[1])},{timestamp},{len(data)}\n" )
			if 1 > len(data):
				with open( os.path.join( self.logfilepath, record0filename ), "a", encoding="utf-8") as f:
					f.write( f"1,{str(tuple_row[0])},{str(tuple_row[1])},{timestamp}\n" )
		except Exception as ex:
			self.write_log( f"Exception happended in Method record_check_zero. Exception = {ex}; center row = {tuple_row}; timestamp = {timestamp}; len = {len(data)}" )
	
	def check_response_data_len( self, response = None ):
		temp_dict = eval( response )
		data = []
		if 'data' in temp_dict.keys():
			data = temp_dict["data"]
		if 0 < len( data ):
			return True
		return False

	def update_input_file(self):
		input_file = os.path.join( self.input_path, self.input )
		center_from_file = {}
		try:
			with open( input_file, 'r', encoding='utf-8') as f:
				for item in f.readlines()[1:]:
					temp_list = item.split(",")
					key = f"{temp_list[1]}___{temp_list[2]}"
					center_from_file[key] = item
		except Exception as ex:
			self.write_log( f"cannot write input_file ({input_file}). Exception = {ex}" )
		else:
			temp_list = []
			item_added = []
			for one_tuple in self.center:
				key = f"{one_tuple[0]}___{one_tuple[1]}"
				if key in center_from_file.keys():
					if 0 == int( one_tuple[2] ) and self.threshold_to_turn1 < int( one_tuple[3] ):
						temp_list.append( f"1,{one_tuple[0]},{one_tuple[1]},1,{one_tuple[3]},{one_tuple[4]}\n" )
					else:
						temp_list.append( f"1,{one_tuple[0]},{one_tuple[1]},{one_tuple[2]},{one_tuple[3]},{one_tuple[4]}\n" )
					item_added.append( key )
				else:
					self.write_log( f"Item in self.center cannot be found in input file. key = {key},{one_tuple[2]},{one_tuple[3]},{one_tuple[4]}" )
			for index, key in enumerate(center_from_file):
				if key not in item_added:
					temp_list.append( f"{center_from_file[key]}" )
			try:
				with open( input_file, 'w', encoding='utf-8') as f:
					f.write( "OBJECTID,x,y,ok0,max,max_timestamp\n" )
					for row in temp_list:
						f.write( row )
			except Exception as ex:
				self.write_log( f"cannot write input_file ({input_file}). Exception = {ex}" )

	def print_attributes(self):
		print( f"self.rootpath = {self.rootpath}; self.input = {self.input}; self.city = {self.city}; self.city_chinese_name = {self.city_chinese_name};" )
		print( f"self.logfilepath = {self.logfilepath}; self.library_path = {self.library_path}; " )
		print( f"self.input_path = {self.input_path}; self.input = {self.input}; self.filename = {self.filename}; " )
		print( f"self.max_proxies = {self.max_proxies}; self.proxy_pwd = {self.proxy_pwd}; self.proxy_user = {self.proxy_user}; " )
		print( f"self.get_cookies_method = {self.get_cookies_method}; self.cookies = {self.cookies}; self.sleeptime_between_cookies = {self.sleeptime_between_cookies}; " )
		print( f"self.browser = {self.browser}; self.use_proxy = {self.use_proxy}; self.delay_time = {self.delay_time}; self.minimal_delay = {self.minimal_delay}; " )
		print( f"self.repeat_request_times_upon_empty_data = {self.repeat_request_times_upon_empty_data}")
		counter = 0
		string = ""
		for one in self.center:
			counter += 1
			string += f"{one}\n"
			if 10 < counter:
				break
		print( f"len of center = {len(self.center)}; first 10 rows = {string}" )

	def exec(self, pickup_last = True):
		time_now = time.time()
		first_time_now_str = time.strftime('%Y%m%d_%H%M%S', time.localtime(time_now))
		self.write_log("start crawling")
		if self.cookies is None or 1 > len( self.cookies ):
			print("reading the first cookie.")
			cookie = self.get_cookie()
		else:
			cookie = self.cookies
		if self.debug:
			print( f"cookie = {cookie}" )
		i = 1
		request_counter = self.request_counter
		
		center, params_list = self.initial_paramslist( pickup_last = pickup_last )
		if self.debug:
			self.print_attributes()
		for index, params in enumerate(params_list):
			while self.cookies is None or 1 > len( self.cookies ):
				self.cookies = None
				self.cookies = self.get_cookie()
				print( f"reading next cookie after {self.sleeptime_between_cookies} seconds.")
				time.sleep( self.sleeptime_between_cookies )

			time_now = time.time()
			time_now_str = time.strftime('%Y%m%d_%H%M%S', time.localtime(time_now))

			#这部分负责每个qq号码抓取的次数
			if request_counter % settings.fre == 0:
				self.cookies = None
				cookie = self.get_cookie()
				if self.debug:
					print(cookie)

			try:
				if self.high_population_densitiy:
					must_have_data = 1
				else:
					must_have_data = int(center[index][2]) # 0 means text['data'] could be empty
				data_gotten = False
				if must_have_data:
					for j in range( self.repeat_request_times_upon_empty_data ):
						if self.use_proxy:
							text = self.spyder_proxy(cookie, params)
						else:
							text = self.spyder(cookie, params)
							if 1 > len( text ):
								self.cookies = None
								self.cookies = self.get_cookie()
							time.sleep( random.randint( self.minimal_delay * 1000, self.delay_time * 1000 ) / 1000 )
						if self.check_response_data_len( text ):
							data_gotten = True
							break
						else:
							print( f"\nthis is number {j} request for index {i} of center; request_counter of this cookie is {request_counter}" )
							request_counter += 1
				else:
					if self.use_proxy:
						text = self.spyder_proxy(cookie, params)
					else:
						text = self.spyder(cookie, params)
						if 1 > len( text ):
							self.cookies = None
							self.cookies = self.get_cookie()
						time.sleep( random.randint( self.minimal_delay * 1000, self.delay_time * 1000 ) / 1000 )
				if index < len( center ):
					self.record_check_zero( text, center[index] ) # this one is for debugging ONLY
					if not must_have_data or data_gotten:
						self.record_finished(center[index])
						self.check_and_update_center( response = text, tuple_row = center[index], index = index )
			except Exception as ex:
				self.write_log( f"Internet connection lost. Exception = {ex}" )
				print( f"Internet connection lost. Exception = {ex}" )
			
			self.view_bar(i, len(params_list))
			i += 1
			request_counter += 1
		if self.need_update_center:
			print( f"\nwe need to update input file" )
			self.update_input_file()
		self.request_counter = request_counter

	def write_log(self, content = None, logfilename = None, content_only = False):
		if content is not None and 0 < len( content ):
			today = datetime.datetime.now().strftime("%Y%m%d")
			if logfilename is None:
				logfilename = f"easygo{today}.log"
			try:
				with open( os.path.join( self.logfilepath, logfilename ),'a',encoding='utf-8') as f:
					if content_only:
						info = f"{str(content)}\n"
					else:
						info = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] {content}\n"
					f.write(info)
				return 1
			except Exception as ex:
				return 0
		return -1

	def view_bar(self, num, total):
		rate = float(num) / float(total)
		rate_num = int(rate * 100)
		r = '\r[%s%s]%d%%' % ("="*(rate_num), " "*(100-rate_num), rate_num, )
		sys.stdout.write(r)

	def check_unfinished_points(self):
		"""
		returns number of unfinished points
		"""
		center = []
		requested = []
		today = datetime.datetime.now().strftime("%Y%m%d")
		input_file_path = os.path.join( self.input_path, self.input )
		finished_input = f"{self.input}{today}.log"
		finished_file_path = os.path.join( self.logfilepath, self.finished_input )
		try:
			with open( input_file_path, 'r', encoding='utf-8') as f:
				for item in f.readlines()[1:]:
					center.append(tuple(item.strip().split(",")[-5:]))
			if os.path.isfile( finished_file_path ):
				with open( finished_file_path, 'r', encoding='utf-8') as log_file:
					for item in log_file.readlines():
						value = item.strip().split(",")
						requested.append( f"{value[0]}___{value[1]}" )
		except Exception as ex:
			print( f"Error in reading {input_file_path} or {finished_file_path}. Exception = {ex}" )
			sys.exit(-3)
		return len( center ) - len( requested )

if __name__ == "__main__":
	high_population_densitiy = settings.high_population_densitiy if hasattr(settings, "high_population_densitiy") else False
	repeat_request_times = [3, 6, 9, 15, 20,]
	
	if high_population_densitiy: # good for guangzhou_south; NOT good for shenzhen
		repeat_request_times = [2,3,]
	request_counter = 1
	cookies = None
	for counter in range( len(repeat_request_times) ):
		app = easygospider(request_counter = request_counter, cookies = cookies)
		app.repeat_request_times_upon_empty_data = repeat_request_times[counter]
		app.exec(pickup_last = True)
		number_ahead = app.check_unfinished_points()
		if 1 > number_ahead:
			break
		else:
			request_counter = app.request_counter
			cookies = app.cookies
			print( f"\nNumber {counter}, there are still {number_ahead} points to be collected." )
