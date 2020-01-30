# coding: utf-8

import requests
from requests.exceptions import RequestException
import json
import time
from time import sleep
import datetime
import sys
import os
import csv
import random
import pandas
import math
import struct
import cv2
import numpy as np
from urllib import parse
from collections.abc import Iterable
from collections.abc import Mapping
from PIL import Image
try:
	from cStringIO import StringIO as BytesIO
except ImportError:
	from io import BytesIO

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains

from baidumaptile.settings import settings

class Bmapm1Spider(object):
	"""
		这个链接是百度地图官网的坐标拾取器http://api.map.baidu.com/lbsapi/getpoint/index.html
		该拾取器采用了目前百度地图的底图；但是文字依然是单独一个图层；因此和百度地图手机app上面的文字大小不一致。
		百度地图官网（http://lbsyun.baidu.com/jsdemo.htm#c1_15）使用了这个javascript渲染套件：https://github.com/pa7/heatmap.js
		http://api.map.baidu.com/staticimage/v2?ak=iL3ZmAje32Q6WrXgaWcBSZP0RZG1hekL&center=113.404,23.052&width=512&height=512&zoom=17
		开发文档：http://lbsyun.baidu.com/index.php?title=static

		百度地图瓦片下载地址类似（其中z是17级）：
		http://online4.map.bdimg.com/tile/?qt=vtile&x=24555&y=5119&z=17&styles=pl&scaler=1&udt=20190718

		墨卡托坐标与LBS应用：https://www.cnblogs.com/charlesblc/p/8394688.html

		百度地图切面(瓦片)像素点和经纬度的关系https://blog.csdn.net/qq2170218/article/details/32916093（本文是错误的）
		nohup python /home/yujx/baidumaptile/bmapm2.py >> bmapm2.log 2>&1 &
	"""
	name = "bmapm1"

	now = None
	today = None
	settings = None
	root_path = None
	log_dir = None
	debug = False
	crawled_dir = None
	output_folder_name = None
	input_folder_name = None
	locator_png_file_name = None
	base_uri = None
	browser = None
	z = -1
	xy_list = []

	city_lng_lat_dict = {}
	city_list = []
	tile_height = -1
	tile_width = -1
	tile_latest_version = None
	tile_lng_lat_csv = None

	loading_wait_time = 3
	loading_check_cycle = 10
	implicitly_wait_time = 60

	def init_self_attributes(self, xy_list = [], four_edge_xy_list = []):
		"""
		revision 20190725
		"""
		self.now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		self.today = datetime.datetime.now().strftime("%Y%m%d")
		self.settings = settings
		self.root_path = self.settings.get( name="PROJECT_PATH", default="" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )
		self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		self.crawled_dir = self.settings.get( name="CRAWLED_DIR", default = "" )
		self.output_folder_name = self.settings.get( name = "OUTPUT_FOLDER_NAME", default="" )
		self.input_folder_name = self.settings.get( name = "INPUT_FOLDER_NAME", default="" )
		self.locator_png_file_name = self.settings.get( name = "LOCATOR_PNG_FILE_NAME", default="" )
		self.base_uri = self.settings.get( name = "BASE_URI", default="" )
		self.browser = self.settings.get( name = "BROWSER", default="" )
		self.z = self.settings.get( name = "LEVEL_Z", default=-1 )
		if isinstance( xy_list, list ) and 0 < len( xy_list ):
			self.xy_list = xy_list
		elif isinstance( four_edge_xy_list, list ) and 0 < len( four_edge_xy_list ):
			self.xy_list = self.get_xy_list_from_four_edges( four_edge_xy_list )
		else:
			self.make_xy_list(4)

		self.city_lng_lat_dict = self.settings.get( name= "CITY_LNG_LAT_DICT", default = {})
		self.city_list = self.settings.get( name= "CITY_LIST", default = [])
		self.tile_height = self.tile_width = 256
		self.tile_latest_version = self.settings.get( name= "LATEST_VERSION", default = "")
		self.tile_lng_lat_csv = self.settings.get( name= "TILE_LNG_LAT_CSV", default = "")

	def __init__(self, xy_list = [], four_edge_xy_list = []):
		self.init_self_attributes( xy_list = xy_list, four_edge_xy_list = four_edge_xy_list )

	def write_log(self, content = None, logfilename = None, content_only = False):
		if isinstance(content, Iterable) and 0 < len( content ):
			today = datetime.datetime.now().strftime("%Y%m%d")
			if logfilename is None:
				logfilename = f"{self.name}_{today}.log"
			try:
				with open( os.path.join( self.log_dir, logfilename ), "a", encoding = "utf-8" ) as log_file:
					if content_only:
						info = f"{content}\n"
					else:
						info = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] {content}\n"
					log_file.write(info)
				return 1
			except Exception as ex:
				print( f"fail to write log. Exception = {ex}" )
				return 0
		return -1

	def get_headers(self, browser = "", cookies = None, referer = None):
		headers = {
			"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
			"Referer": "http://api.map.baidu.com/lbsapi/getpoint/index.html",
			"X-Requested-With": "XMLHttpRequest",
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
			"Accept-Encoding": "gzip, deflate",
			"Accept-Language": "en-US,en;q=0.9",
			"Cache-Control": "max-age=0",
		}
		if cookies is not None:
			headers["Cookie"] = cookies
		if referer is not None:
			headers["Referer"] = referer
		if not isinstance( browser, str ) or 1 > len( browser ):
			browser = self.browser

		if "Chrome" == self.browser:
			pass
		elif "ChromePC" == self.browser:
			headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"
		return headers

	def webdriver_zoom(self, chrome_driver = None, level_int = 16 ):
		"""
			revision: 20190809, 20190801, 20190731
		"""
		try:
			level = int( chrome_driver.find_element_by_id( "ZoomNum" ).text )
			counter = 20
			while level_int != level:
				if level_int > level:
					zoom_div = self.get_zoom_element( chrome_driver = chrome_driver, zoom_in_or_zoom_out = "in")
					if zoom_div is not None: zoom_div.click()
				elif level_int < level:
					zoom_div = self.get_zoom_element( chrome_driver = chrome_driver, zoom_in_or_zoom_out = "out")
					if zoom_div is not None: zoom_div.click()
				time.sleep(0.5)
				level = int( chrome_driver.find_element_by_id( "ZoomNum" ).text )
				counter -= 1
				if 0 > counter:
					break
			return level
		except WebDriverException as ex:
			self.write_log( f"WebDriverException happended while getting find_element_by_id. WebDriverException = {ex}" )
		except Exception as ex:
			self.write_log( f"WebDriverException happended while getting find_element_by_id. Exception = {ex}" )
		
		return -1

	def get_zoom_element(self, chrome_driver = None, zoom_in_or_zoom_out = "out"):
		"""
		revision 20190731
		"""
		return_none = False
		try:
			if "in" == zoom_in_or_zoom_out:
				zoom_div = chrome_driver.find_element_by_xpath( '//div[@class="BMap_button BMap_stdMpZoomIn"]/div[@class="BMap_smcbg"]' )
			elif "out" == zoom_in_or_zoom_out:
				zoom_div = chrome_driver.find_element_by_xpath( '//div[@class="BMap_button BMap_stdMpZoomOut"]/div[@class="BMap_smcbg"]' )
		except WebDriverException as ex1:
			try:
				if "in" == zoom_in_or_zoom_out:
					zoom_div = chrome_driver.find_element_by_xpath( '//div[@class="BMap_button BMap_stdMpZoomIn"]' )
				elif "out" == zoom_in_or_zoom_out:
					zoom_div = chrome_driver.find_element_by_xpath( '//div[@class="BMap_button BMap_stdMpZoomOut"]' )
			except WebDriverException as ex:
				return_none = True
				# WebDriverException = Message: no such element: Unable to locate element: {"method":"xpath","selector":"//div[@class="NoSuchClass"]"}
			except Exception as ex:
				return_none = True
		except Exception as ex:
			return_none = True

		if return_none:
			error_msg = "\"BMap_button BMap_stdMpZoomIn\"" if "in" == zoom_in_or_zoom_out else "\"BMap_button BMap_stdMpZoomOut\""
			error_msg = f"cannot find zoom_in element using css class \"BMap_smcbg\" nor {error_msg}; Exception = {ex}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return None
		return zoom_div

	def extract_xyz_from_url(self, url = ""):
		"""
		url of one tile, similar to this one:
			https://gss0.bdstatic.com/8bo_dTSlRcgBo1vgoIiO_jowehsv/tile/?qt=vtile&x=12291&y=2571&z=16&styles=pl&scaler=1&udt=20190726
		revision 20190731
		"""
		try:
			url_object = parse.urlparse( url )
			query_dict = parse.parse_qs( url_object.query )
			return (query_dict["x"][0], query_dict["y"][0], query_dict["z"][0])
		except Exception as ex:
			error_msg = f"fail to parse {url}. Exception = {ex}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return (-1, -1, -1)

	def download_tiles_from_getpoint(self, chrome_driver = None, lng_lat = ""):
		"""
		download all tile image files on current page at http://api.map.baidu.com/lbsapi/getpoint/index.html
		https://gss0.bdstatic.com/8bo_dTSlR1gBo1vgoIiO_jowehsv/tile/?qt=vtile&x=12158&y=2388&z=16&styles=pl&scaler=1&udt=20190726
		revision 20190731
		"""
		file_name_list = []
		if chrome_driver is None or not hasattr( chrome_driver, "find_elements_by_xpath" ):
			error_msg = f"bad chrome_driver {chrome_driver}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return file_name_list
		image_list = chrome_driver.find_elements_by_xpath( '//div[@id="MapHolder"]/div/div[@class="BMap_mask"]/following-sibling::div/following-sibling::div/div/img' )
		link_list = []
		for one_src in image_list:
			link_list.append( one_src.get_attribute("src") )

		headers = self.get_headers(self.browser)
		lng_lat_folder_name = lng_lat.replace(",", "_")
		if not os.path.isdir( os.path.join( self.crawled_dir, lng_lat_folder_name ) ):
			os.makedirs( os.path.join( self.crawled_dir, lng_lat_folder_name ) )

		if 0 < len( link_list ): self.update_tile_latest_version( url = link_list[0] )
		for url in link_list:
			x, y, z = self.extract_xyz_from_url( url = url )
			response = requests.get( url, headers = headers )
			image = None
			if hasattr( response, "status_code") and 200 == response.status_code and hasattr( response, "content" ):
				try:
					image = Image.open( BytesIO( response.content ) )
					filename = f"{x}_{y}_{z}.{image.format.lower()}"
					file_name_list.append(filename)
					file_path = os.path.join( self.crawled_dir, lng_lat_folder_name, filename )
					with open( file_path, "wb" ) as file:
						file.write(response.content)
				except Exception as ex:
					error_msg = f"wrong response.content ({response.content}). Exception = {ex}"
					self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			else:
				error_msg = f"wrong response ({response})"
				self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		return file_name_list

	def update_tile_latest_version(self, url = ""):
		"""
		url example:
		https://gss0.bdstatic.com/8bo_dTSlR1gBo1vgoIiO_jowehsv/tile/?qt=vtile&x=12158&y=2388&z=16&styles=pl&scaler=1&udt=20190726
		revision 20190802
		"""
		try:
			url_object = parse.urlparse( url )
			query_dict = parse.parse_qs( url_object.query )
			date_str = query_dict["udt"]
			if isinstance( date_str, str ) and 8 == len( date_str ):
				self.tile_latest_version = date_str
		except Exception as ex:
			error_msg = f"cannot parse {url}, Exception = {ex}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )

	def get_element_rect(sefl, chrome_driver = None, xpath_str = '//div[@id="MapHolder"]', return_rect = True ):
		"""
		Description:
			return a dict, including this element's size or rect information
		revision: 20190731
		Usage:
			rect_dict = self.get_element_rect( chrome_driver = chrome_driver, xpath_str = '//div[@id="MapHolder"]', return_rect = True )
		"""
		rect_dict = {}
		if chrome_driver is None or not hasattr( chrome_driver, "find_element_by_xpath" ):
			error_msg = f"bad chrome_driver {chrome_driver}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return rect_dict

		map_holder_div = chrome_driver.find_element_by_xpath( xpath_str )
		if return_rect and hasattr( map_holder_div, "rect"):
			return map_holder_div.rect # {'height': 786, 'width': 1640, 'x': 0, 'y': 139}
		elif return_rect:
			error_msg = f"bad map_holder_div {map_holder_div}; dir = {dir(map_holder_div)}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return rect_dict

		if hasattr( map_holder_div, "size" ):
			return map_holder_div.size
		else:
			error_msg = f"bad map_holder_div {map_holder_div}; dir = {dir(map_holder_div)}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return rect_dict

	def check_response( self, webdriver = None, id_str = "" ):
		"""
		检查页面是否加载完成
		"""
		element_input = None
		counter = 0
		while element_input is None:
			if counter > self.loading_check_cycle:
				return False
			try:
				element_input = webdriver.find_element_by_id( id_str )
			except NoSuchElementException as ex:
				element_input = None
			except Exception as ex:
				element_input = None
			sleep( self.loading_wait_time )
			counter += 1

		return True

	def save_located_map(self, chrome_driver = None, lng_lat = "113.05917,23.16048", level_int = 16):
		"""
		Description:
			在http://api.map.baidu.com/lbsapi/getpoint/index.html页面输入经纬度并调整到level_int并截屏
		revision: 20190809, 20190731
		"""
		png_file_name = ""
		png_image_path = ""

		input_box_id = "localvalue"
		if not self.check_response( webdriver = chrome_driver, id_str = input_box_id ):
			return None, png_file_name, png_image_path

		chrome_driver.find_element_by_id( input_box_id ).clear()
		chrome_driver.find_element_by_id( input_box_id ).send_keys(lng_lat)
		sleep(0.2)
		check_element = chrome_driver.find_element_by_id( "pointLabel" )
		if not check_element.is_selected(): check_element.click()
		sleep(0.2)
		chrome_driver.find_element_by_id( "localsearch" ).click()
		sleep(0.2)

		png_file_name = ""
		png_image_path = ""

		# by default, it will show a map at Level 15
		level = 0
		if -1 < level_int:
			level = self.webdriver_zoom( chrome_driver = chrome_driver, level_int = level_int )
			chrome_driver.implicitly_wait( self.implicitly_wait_time )
		
		if -1 == level_int or level == level_int:
			png_image = chrome_driver.get_screenshot_as_png()
			lng_lat_list = lng_lat.split(",")
			z = 15 if -1 == level_int else level
			lng = lat = "10000"
			if isinstance( lng_lat_list, list ) and 2 == len( lng_lat_list ):
				lng = lng_lat_list[0]
				lat = lng_lat_list[1]
			png_file_name = f"locator___{lng}___{lat}___{z}.png"
			png_image_path = os.path.join( self.crawled_dir, png_file_name )
			try:
				with open( png_image_path, "wb" ) as png_file:
					png_file.write( png_image )
			except Exception as ex:
				error_msg = f"fail to write {png_image_path}; Exception = {ex}"
				self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
				return None, png_file_name, png_image_path
			return png_image, png_file_name, png_image_path
		else:
			error_msg = f"wrong level_int ({level_int}) or wrong level ({level})"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return None, png_file_name, png_image_path

	def webdriver_operation_debug(self, url = None, browser = "ChromePC", city = "广州", level_int = 16):
		header_dict = self.get_headers(browser)
		chrome_options = Options()
		chrome_options.add_argument( f"accept={header_dict['Accept']}" )
		chrome_options.add_argument( f"referer={header_dict['Referer']}" )
		chrome_options.add_argument( f"user-agent={header_dict['User-Agent']}" )
		chrome_options.add_argument( f"lang={header_dict['Accept-Language']}" )
		chrome_driver = webdriver.Chrome( options=chrome_options, executable_path="chromedriver.exe" ) # 先将chromedriver.exe放置在PATH内
		chrome_driver.implicitly_wait(30)
		chrome_driver.get( url )
		element = chrome_driver.find_element_by_xpath( '//div[@class="col-md-8"]/div[@class="quote"]/span[@class="text"]/following-sibling::span/small' )
		prop = element.get_property("itemprop")
		attr = element.get_attribute("itemprop")
		a_element = chrome_driver.find_element_by_xpath( '//div[@class="col-md-8"]/div[@class="quote"]/span[@class="text"]/following-sibling::span/a' )
		print( f"attr = {attr}; type = {type(attr)}; prop = {prop}; element = {element}" )
		rect_dict = a_element.rect
		click_dict = {
			"x": rect_dict["x"] + 10,
			"y": rect_dict["y"] + 10,
		}
		print( click_dict )
		ActionChains( chrome_driver ).move_by_offset( click_dict["x"], click_dict["y"] ).click().perform()
		# a_element.click()
		sleep(35)

	def get_four_edge_xy_num( self, file_name_list = []):
		"""
		file_name_list looks like this:
			["12310_2568_16.png", "12310_2569_16.png", ]
		"""
		x_list = []
		y_list = []
		try:
			for one_file_name in file_name_list:
				file_name_fragment_list = one_file_name.split("_")
				if 3 == len( file_name_fragment_list ):
					x_list.append( int(file_name_fragment_list[0]) )
					y_list.append( int(file_name_fragment_list[1]) )
				else:
					error_msg = f"wrong file_name_fragment_list length ({file_name_fragment_list})"
					self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			min_x, min_y, max_x, max_y = min( x_list ), min( y_list ), max( x_list ), max( y_list )
		except Exception as ex:
			error_msg = f"fail to generate file_name_fragment_list; Exception = {ex}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return (-1, -1, -1, -1)
		return (min_x, min_y, max_x, max_y)
	
	def cut_one_image(self, png_image_path = "" ):
		"""
			在全屏以后，得到地图区域标尺如下：map_holder_div.rect
			根据{'height': 786, 'width': 1640, 'x': 0, 'y': 139}，就是应该使用image[ 139:, :1640 ]
			切图例子：return locator[5:89, 500:630]#截取第5行到89行的第500列到630列的区域：y在前；x在后
		References:
			https://www.jianshu.com/p/0633ead5613c
		revision: 20190801, 20190802
		删除locator = None, 经过测试发现locator_image = Image.open( BytesIO( locator ) )以后locator_image
		"""
		new_image_path = png_image_path.replace(".png", "___cut.png")
		image = cv2.imread( png_image_path )
		new_image = image[ 139:, :1640 ]
		cv2.imwrite( new_image_path, new_image )
		return new_image

	def get_xy_from_locator_image(self, png_image = None ):
		"""
			使用缺省的红点图片(LOCATOR_PNG_FILE_NAME, locator.png)查看
		revision: 20190802, 20190801
		删除locator = None, 经过测试发现locator_image = Image.open( BytesIO( locator ) )以后locator_image
		"""
		x, y = -1, -1
		if png_image is None:
			return (x, y)
		template_path = os.path.join( self.root_path, self.input_folder_name, self.locator_png_file_name )
		template = cv2.imread( template_path )
		if template is None or not hasattr(template, "shape"):
			return (x, y)
		top_left, bottom_right, img, seconds = self.find_image_in_the_whole( whole_image = png_image, template = template, save_result = False, result_file_path = None, show_result = False, show_window = None )
		# print( f"top_left = {top_left}, bottom_right = {bottom_right}" )
		# top_left = (813, 376) bottom_right = (826, 394)
		if 13 != int(bottom_right[0] - top_left[0]):
			return (x, y)
		return ( top_left[0] + 7, bottom_right[1] ) # bottom_right[1] is larger than top_left[1]

	def get_lng_lat_from_tile(self, location_dict = {}):
		"""
		revision: 20190802
		"min_tile_x", "min_tile_y", "max_tile_x", "max_tile_y" indicate where the cut_locator_image in the tile-stacked whole map
		"locator_x", "locator_y" indicate where the poiter is on the cut_locator_image
		"tile_min_x", "tile_min_y", "tile_max_x", "tile_max_y" are tile numbers
		location_dict = {
			"locator_x": x,
			"locator_y": y,
			"min_tile_x": top_left[0],
			"min_tile_y": top_left[1],
			"max_tile_x": bottom_right[0],
			"max_tile_y": bottom_right[1],
			"tile_min_x": min_x,
			"tile_min_y": min_y,
			"tile_max_x": max_x,
			"tile_max_y": max_y,
			"lng_lat": lng_lat,
		}

		print( f"height = {height}; x = {x}; y = {y}; y floor = {math.floor(y / self.tile_height)}; minus = {y / self.tile_height}" )
		{'locator_x': 820, 'locator_y': 394, 'min_tile_x': 229, 'min_tile_y': 153, 'max_tile_x': 1869, 'max_tile_y': 940, 
		'tile_min_x': 12154, 'tile_min_y': 2386, 'tile_max_x': 12161, 'tile_max_y': 2389, 'lng_lat': '111.838095,21.578807'}
		height = 1024; x = 1049; y = 477; y floor = 1; minus = 1.86328125
		{'111.838095,21.578807': {'tile_x_number': 12158, 'tile_y_number': 2387, 'x_from_left_in_this_tile': 25, 'y_from_bottom_in_this_tile': 221}}

		width = location_dict["tile_max_x"] - location_dict["tile_min_x"] + 1
		width *= self.tile_width

		百度地图在中国的y是向北增大；在北纬上面y值越大北纬越高（正好和opencv相反）；x则是随着东经向东增大
		"""
		mapper_dict = {}
		try:
			height = location_dict["tile_max_y"] - location_dict["tile_min_y"] + 1
			height *= self.tile_height
			x = location_dict["locator_x"] + location_dict["min_tile_x"]
			y = height - (location_dict["locator_y"] + location_dict["min_tile_y"])
			tile_x_number = math.floor(x / self.tile_width) + location_dict["tile_min_x"] # 从左向右计数
			tile_y_number = math.floor(y / self.tile_height) + location_dict["tile_min_y"] # 从下向上计数
			x_from_left_in_this_tile = x % self.tile_width
			y_from_bottom_in_this_tile = y % self.tile_height
			lng_lat_list = location_dict["lng_lat"].split(",")
			if 2 == len( lng_lat_list ):
				mapper_dict = {
					"tile_x_number": tile_x_number,
					"tile_y_number": tile_y_number,
					"x_from_left_in_this_tile": x_from_left_in_this_tile,
					"y_from_bottom_in_this_tile": y_from_bottom_in_this_tile,
					"lng": float(lng_lat_list[0]),
					"lat": float(lng_lat_list[1]),
				}
		except Exception as ex:
			error_msg = f"cannot find pointer's lng or lat; Exception = {ex}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			mapper_dict = {}
		finally:
			return mapper_dict

	def calculate_tile_lng_lat(self, mapping_dict = {} ):
		"""
		revision: 20190809,20190802
		mapping_dict:
		{
			'111.838095,21.578807': {'tile_x_number': 12158, 'tile_y_number': 2387, 'x_from_left_in_this_tile': 25, 'y_from_bottom_in_this_tile': 221, 'lng': 111.838095, 'lat': 21.578807}, 
			'114.706195,23.740876': {'tile_x_number': 12469, 'tile_y_number': 2641, 'x_from_left_in_this_tile': 63, 'y_from_bottom_in_this_tile': 134, 'lng': 114.706195, 'lat': 23.740876}
		}
		"""
		try:
			if 2 > len( mapping_dict ):
				error_msg = f"At least two points are needed."
				self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
				return ([], 0.0, 0.0)

			mapping_key_list = list( mapping_dict.keys() )
			for index, key in enumerate( mapping_dict ):
				if 0 == index:
					continue
				last_key = mapping_key_list[ index - 1 ]
				first_point = mapping_dict[ last_key ]
				second_point = mapping_dict[ key ]
				print( first_point, second_point )
				delta_lng = abs( first_point["lng"] - second_point["lng"] )
				delta_lat = abs( first_point["lat"] - second_point["lat"] )
				delta_tile_x = abs( first_point["tile_x_number"] - second_point["tile_x_number"] )
				delta_tile_y = abs( first_point["tile_y_number"] - second_point["tile_y_number"] )
				if first_point["tile_x_number"] < second_point["tile_x_number"]:
					delta_pixel_x = delta_tile_x * self.tile_width + second_point["x_from_left_in_this_tile"] - first_point["x_from_left_in_this_tile"]
				else:
					delta_pixel_x = delta_tile_x * self.tile_width + first_point["x_from_left_in_this_tile"] - second_point["x_from_left_in_this_tile"]
				
				if first_point["tile_y_number"] < second_point["tile_y_number"]:
					delta_pixel_y = delta_tile_y * self.tile_height + second_point["y_from_bottom_in_this_tile"] - first_point["y_from_bottom_in_this_tile"]
				else:
					delta_pixel_y = delta_tile_y * self.tile_height + first_point["y_from_bottom_in_this_tile"] - second_point["y_from_bottom_in_this_tile"]
				
				x_ratio = delta_lng / delta_pixel_x
				y_ratio = delta_lat / delta_pixel_y
				first_tile = {
					"left_lng": first_point["lng"] - first_point["x_from_left_in_this_tile"] * x_ratio,
					"bottom_lat": first_point["lat"] - first_point["y_from_bottom_in_this_tile"] * y_ratio,
					"tile_x_number": first_point["tile_x_number"],
					"tile_y_number": first_point["tile_y_number"],
				}

				second_tile = {
					"left_lng": second_point["lng"] - second_point["x_from_left_in_this_tile"] * x_ratio,
					"bottom_lat": second_point["lat"] - second_point["y_from_bottom_in_this_tile"] * y_ratio,
					"tile_x_number": second_point["tile_x_number"],
					"tile_y_number": second_point["tile_y_number"],
				}
				print( first_tile, second_tile )

				if 1 < index:
					break # we ONLY pick the first two points for calculation

			two_point_list = [first_tile, second_tile,]
			return two_point_list, x_ratio, y_ratio
		except Exception as ex:
			error_msg = f"cannot calculate lng or lat of tiles; Exception = {ex}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return ([], 0.0, 0.0)

	def save_this_tile_information(self, two_point_list = [], x_ratio = 0.0, y_ratio = 0.0, z = -1, city = "" ):
		"""
		revision: 20190809,
			two_point_list = [{
				"left_lng": first_point["lng"] - first_point["x_from_left_in_this_tile"] * x_ratio,
				"bottom_lat": first_point["lat"] - first_point["y_from_bottom_in_this_tile"] * y_ratio,
				"tile_x_number": first_point["tile_x_number"],
				"tile_y_number": first_point["tile_y_number"],
			}, {
				"left_lng": second_point["lng"] - second_point["x_from_left_in_this_tile"] * x_ratio,
				"bottom_lat": second_point["lat"] - second_point["y_from_bottom_in_this_tile"] * y_ratio,
				"tile_x_number": second_point["tile_x_number"],
				"tile_y_number": second_point["tile_y_number"],
			}]
		"""
		first_tile = two_point_list[0]
		second_tile = two_point_list[1]
		row_dict = {
			"left_lng1": first_tile["left_lng"],
			"bottom_lat1": first_tile["bottom_lat"],
			"tile_x_number1": first_tile["tile_x_number"],
			"tile_y_number1": first_tile["tile_y_number"],
			"left_lng2": second_tile["left_lng"],
			"bottom_lat2": second_tile["bottom_lat"],
			"tile_x_number2": second_tile["tile_x_number"],
			"tile_y_number2": second_tile["tile_y_number"],
			"x_ratio": x_ratio,
			"y_ratio": y_ratio,
			"z": z,
			"city": city,
			"tile_latest_version": self.tile_latest_version,
			"server": socket.gethostname(),
			"date": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
		}

		file_path = os.path.join( self.root_path, self.input_folder_name, self.tile_lng_lat_csv )
		self.append_row( key_list = row_dict.keys(), item_list = row_dict.values(), csv_file_path_str = file_path )
	
	def append_row(self, key_list = [], item_list = [], csv_file_path_str = "" ):
		try:
			new_file = False
			if not os.path.isfile( csv_file_path_str ):
				new_file = True
			with open( csv_file_path_str, "a", encoding="utf-8", newline="") as f:
				writer = csv.writer(f)
				if new_file:
					writer.writerow( key_list )
				writer.writerow( item_list )
		except Exception as ex:
			self.write_log( f"cannot write into file {csv_file_path_str}; content is: {item_list}; Exception = {ex}" )
			return False
		else:
			return True

	def webdriver_operation(self, url = None, browser = "ChromePC", city = "广州", level_int = 16):
		"""
		references:
			https://sites.google.com/a/chromium.org/chromedriver/capabilities
			https://peter.sh/experiments/chromium-command-line-switches/
			dir(webdriver):
			['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__enter__', '__eq__', '__exit__', '__format__', '__ge__', '__getattribute__', 
			'__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', 
			'__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_file_detector', '_is_remote', '_mobile', '_switch_to', 
			'_unwrap_value', '_web_element_cls', '_wrap_value', 'add_cookie', 'application_cache', 'back', 'capabilities', 'close', 'command_executor', 
			'create_options', 'create_web_element', 'current_url', 'current_window_handle', 'delete_all_cookies', 'delete_cookie', 'desired_capabilities', 
			'error_handler', 'execute', 'execute_async_script', 'execute_cdp_cmd', 'execute_script', 'file_detector', 'file_detector_context', 'find_element', 
			'find_element_by_class_name', 'find_element_by_css_selector', 'find_element_by_id', 'find_element_by_link_text', 'find_element_by_name', 
			'find_element_by_partial_link_text', 'find_element_by_tag_name', 'find_element_by_xpath', 'find_elements', 'find_elements_by_class_name', 
			'find_elements_by_css_selector', 'find_elements_by_id', 'find_elements_by_link_text', 'find_elements_by_name', 'find_elements_by_partial_link_text', 
			'find_elements_by_tag_name', 'find_elements_by_xpath', 'forward', 'fullscreen_window', 'get', 'get_cookie', 'get_cookies', 'get_log', 
			'get_network_conditions', 'get_screenshot_as_base64', 'get_screenshot_as_file', 'get_screenshot_as_png', 'get_window_position', 'get_window_rect', 
			'get_window_size', 'implicitly_wait', 'launch_app', 'log_types', 'maximize_window', 'minimize_window', 'mobile', 'name', 'orientation', 
			'page_source', 'quit', 'refresh', 'save_screenshot', 'service', 'session_id', 'set_network_conditions', 'set_page_load_timeout', 
			'set_script_timeout', 'set_window_position', 'set_window_rect', 'set_window_size', 'start_client', 'start_session', 'stop_client', 'switch_to', 
			'switch_to_active_element', 'switch_to_alert', 'switch_to_default_content', 'switch_to_frame', 'switch_to_window', 'title', 'w3c', 'window_handles']
			dir(WebElement):
			['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', 
			'__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', 
			'__str__', '__subclasshook__', '__weakref__', '_execute', '_id', '_parent', '_upload', '_w3c', 'clear', 'click', 'find_element', 
			'find_element_by_class_name', 'find_element_by_css_selector', 'find_element_by_id', 'find_element_by_link_text', 'find_element_by_name', 
			'find_element_by_partial_link_text', 'find_element_by_tag_name', 'find_element_by_xpath', 'find_elements', 'find_elements_by_class_name', 
			'find_elements_by_css_selector', 'find_elements_by_id', 'find_elements_by_link_text', 'find_elements_by_name', 'find_elements_by_partial_link_text', 
			'find_elements_by_tag_name', 'find_elements_by_xpath', 'get_attribute', 'get_property', 'id', 'is_displayed', 'is_enabled', 'is_selected', 'location', 
			'location_once_scrolled_into_view', 'parent', 'rect', 'screenshot', 'screenshot_as_base64', 'screenshot_as_png', 'send_keys', 'size', 'submit', 
			'tag_name', 'text', 'value_of_css_property']
		"""
		if not isinstance( url, str ) or 1 > len(url):
			return False
		chrome_driver = None
		header_dict = self.get_headers(browser)
		all_cities = list( self.city_lng_lat_dict.keys() )
		lng_lat_list = []
		for city in self.city_list:
			if city in all_cities:
				four_value_dict = self.city_lng_lat_dict[city]
				min_lng = four_value_dict["min_lng"]
				min_lat = four_value_dict["min_lat"]
				max_lng = four_value_dict["max_lng"]
				max_lat = four_value_dict["max_lat"]
				lng_lat_list.append( f"{min_lng},{min_lat}" )
				lng_lat_list.append( f"{max_lng},{max_lat}" )

		if 1 > len( lng_lat_list ):
			return False
		
		try:
			chrome_options = Options()
			chrome_options.add_argument( f"accept={header_dict['Accept']}" )
			chrome_options.add_argument( f"referer={header_dict['Referer']}" )
			chrome_options.add_argument( f"user-agent={header_dict['User-Agent']}" )
			chrome_options.add_argument( f"lang={header_dict['Accept-Language']}" )
			# chrome_options.add_argument('--headless') # 在广州分公司将无头配置项注销掉，直接在windows下运行
			chrome_driver = webdriver.Chrome( options=chrome_options, executable_path="chromedriver.exe" ) # 先将chromedriver.exe放置在PATH内
			chrome_driver.implicitly_wait(30)
			chrome_driver.get( url )
			cookies = chrome_driver.get_cookies()
			chrome_driver.maximize_window()
			url_back = chrome_driver.current_url
			title = chrome_driver.title
			mapping_dict = {}
			show_result = True
			for lng_lat in lng_lat_list:
				png_image_bytes, png_file_name, png_image_path = self.save_located_map( chrome_driver = chrome_driver, lng_lat = lng_lat, level_int = level_int)
				if png_image_bytes is not None:
					file_name_list = self.download_tiles_from_getpoint(chrome_driver = chrome_driver, lng_lat = lng_lat)
					min_x, min_y, max_x, max_y = self.get_four_edge_xy_num( file_name_list = file_name_list )
					new_xy_list = self.get_tile_xy_file_name_list( tile_dir = None, filename_list = file_name_list, batch_size = 0 )
					batch_tuple = (min_x, min_y)
					lng_lat_folder_name = lng_lat.replace(",", "_")
					tile_dir = os.path.join( self.crawled_dir, lng_lat_folder_name )
					whole_image_from_all_tiles = self.stack_one_batch( new_xy_list = new_xy_list, tile_dir = tile_dir, save_result = True, z = level_int, batch_tuple = batch_tuple, show_image = True )
					
					cut_locator_image = self.cut_one_image( png_image_path = png_image_path )
					if cut_locator_image is not None:
						x, y = self.get_xy_from_locator_image( png_image = cut_locator_image )
					if whole_image_from_all_tiles is not None and cut_locator_image is not None:
						result_file_path = png_image_path.replace(".png", "___TM_CCOEFF.png")
						top_left, bottom_right, img, seconds = self.find_image_in_the_whole( whole_image = whole_image_from_all_tiles, template = cut_locator_image, save_result = True, result_file_path = result_file_path, show_result = show_result, show_window = png_file_name )
						location_dict = {
							"locator_x": x,
							"locator_y": y,
							"min_tile_x": top_left[0],
							"min_tile_y": top_left[1],
							"max_tile_x": bottom_right[0],
							"max_tile_y": bottom_right[1],
							"tile_min_x": min_x,
							"tile_min_y": min_y,
							"tile_max_x": max_x,
							"tile_max_y": max_y,
							"lng_lat": lng_lat,
						}
						mapping_dict[lng_lat] = self.get_lng_lat_from_tile(location_dict = location_dict)
					sleep(15)
				else:
					self.write_log( f"result from self.save_located_map, png_image = None" )
			two_point_list, x_ratio, y_ratio = self.calculate_tile_lng_lat( mapping_dict = mapping_dict )
			if 1 < len(two_point_list): self.save_this_tile_information( two_point_list = two_point_list, x_ratio = x_ratio, y_ratio = y_ratio, z = level_int, city = city )
			if show_result:	cv2.waitKey(0)
		except WebDriverException as ex:
			self.write_log( f"WebDriverException happended while getting cookies. WebDriverException = {ex}" )
		finally:
			try:
				if chrome_driver is not None:
					chrome_driver.close()
					chrome_driver.quit()
			except Exception as ex:
				self.write_log( f"Exception happended while closing chrome_driver in Method get_cookie.; Exception = {ex}" )

	def get_xy_list_from_four_edges(self, four_edge_xy_list = []):
		temp_list = []
		if not isinstance( four_edge_xy_list, list ) or 2 > len( four_edge_xy_list ):
			return temp_list
		if not isinstance( four_edge_xy_list[0], tuple ) or 2 > len( four_edge_xy_list[0] ):
			return temp_list
		if not isinstance( four_edge_xy_list[1], tuple ) or 2 > len( four_edge_xy_list[1] ):
			return temp_list
		x_start, y_start = four_edge_xy_list[0]
		x_end, y_end = four_edge_xy_list[1]
		x1 = min([x_start, x_end,])
		x2 = max([x_start, x_end,])
		y1 = min([y_start, y_end,])
		y2 = max([y_start, y_end,])
		
		for i in range( x2 - x1 + 1 ):
			for j in range( y2 - y1 + 1 ):
				temp_list.append( (i + x1, j + y1) )
		return temp_list
				
	def request_and_save(self, z = -1):
		"""
		return a list []
		revision: 20190725
		https://gss0.bdstatic.com/8bo_dTSlRsgBo1vgoIiO_jowehsv/tile/?qt=vtile&x=12328&y=2560&z=16&styles=pl&scaler=1&udt=20190723
		"""
		if -1 == z:
			z = self.z
		headers = self.get_headers(self.browser)
		for xy in self.xy_list:
			x = xy[0]
			y = xy[1]
			url = f"{self.base_uri}&x={x}&y={y}&z={z}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, requesting {url}" )
			response = requests.get( url, headers = headers ) # , cookies=cookie, params=params
			# self.write_log( response )
			image = None
			"""
			self.write_log(dir(response))
			[
				'__attrs__', '__bool__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__enter__', '__eq__', '__exit__', '__format__', 
				'__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__iter__', '__le__', '__lt__', 
				'__module__', '__ne__', '__new__', '__nonzero__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', 
				'__str__', '__subclasshook__', '__weakref__', '_content', '_content_consumed', '_next', 'apparent_encoding', 'close', 'connection', 
				'content', 'cookies', 'elapsed', 'encoding', 'headers', 'history', 'is_permanent_redirect', 'is_redirect', 'iter_content', 'iter_lines', 
				'json', 'links', 'next', 'ok', 'raise_for_status', 'raw', 'reason', 'request', 'status_code', 'text', 'url'
			]
			"""
			if hasattr( response, "status_code") and 200 == response.status_code and hasattr( response, "content" ):
				try:
					image = Image.open( BytesIO( response.content ) )
					filename = f"{x}_{y}_{z}.{image.format.lower()}"
					file_path = os.path.join( self.crawled_dir, filename )
					with open( file_path, "wb" ) as file:
						file.write(response.content)
				except Exception as ex:
					error_msg = f"wrong response.content ({response.content}). Exception = {ex}"
					self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			else:
				error_msg = f"wrong response ({response})"
				self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )

	def transfer_lng_lat(self, lng = 113, lat = 23):
		"""
			通过手工寻找得到(113,23)在https://gss0.bdstatic.com/8bo_dTSlQ1gBo1vgoIiO_jowehsv/tile/?qt=vtile&x=3071&y=638&z=14&styles=pl&scaler=1&udt=20190718
			或者是：https://gss0.bdstatic.com/8bo_dTSlR1gBo1vgoIiO_jowehsv/tile/?qt=vtile&x=24568&y=5107&z=17&styles=pl&scaler=1&udt=20190718

			通过手工查找珠江三角洲的四至如下：
			西北角广东省肇庆市德清县莫村中学（这里纬度还太低了）112.123244,23.411807
			https://gss0.bdstatic.com/8bo_dTSlRcgBo1vgoIiO_jowehsv/tile/?qt=vtile&x=24378&y=5204&z=17&styles=pl&scaler=1&udt=20190718
			https://gss0.bdstatic.com/8bo_dTSlRcgBo1vgoIiO_jowehsv/tile/?qt=vtile&x=3047&y=650&z=14&styles=pl&scaler=1&udt=20190718
			西南角闸坡农贸市场111.838095,21.578807
			https://gss0.bdstatic.com/8bo_dTSlRMgBo1vgoIiO_jowehsv/tile/?qt=vtile&x=24316&y=4775&z=17&styles=pl&scaler=1&udt=20190718
			https://gss0.bdstatic.com/8bo_dTSlR1gBo1vgoIiO_jowehsv/tile/?qt=vtile&x=3039&y=596&z=14&styles=pl&scaler=1&udt=20190718
			东北角河源市源城区人民法院114.706195,23.740876
			https://gss0.bdstatic.com/8bo_dTSlRMgBo1vgoIiO_jowehsv/tile/?qt=vtile&x=24939&y=5282&z=17&styles=pl&scaler=1&udt=20190718
			https://gss0.bdstatic.com/8bo_dTSlRcgBo1vgoIiO_jowehsv/tile/?qt=vtile&x=3117&y=660&z=14&styles=pl&scaler=1&udt=20190718
		"""
		y_delta = 0
		x_delta = 0
		if 14 == self.z:
			y_delta = - 5
			x_delta = 0
		elif 17 == self.z:
			y_delta = -33
			x_delta = 2
		coordinate_obj = LngLatTransfer()
		x, y = coordinate_obj.BD09_to_WGS84( bd_lng = lng, bd_lat = lat )
		x, y = coordinate_obj.WGS84_to_WebMercator( lng = x, lat = y )
		divisor = 256 * math.pow( 2, 18 - 14 )
		x2 = math.ceil( x / divisor ) + 0
		y2 = math.ceil( y / divisor ) - 5
		self.write_log( f"Level 14: x = {x2}, y = {y2}" )
		# divisor = 256 * math.pow( 2, 18 - self.z )
		divisor = 256 * math.pow( 2, 18 - self.z )
		x = math.ceil( x / divisor ) + x_delta
		y = math.ceil( y / divisor ) + y_delta
		return ( x, y )

	def make_xy_list(self, z = 4):
		xy_list = []
		if 4 != z:
			self.write_log( "we only make level 4 xy_list" )
			return xy_list

		for x_i in range(10):
			for y_j in range(11):
				new_x = x_i - 5
				new_y = y_j - 6
				x_str = f"m{abs(new_x)}" if 0 > new_x else f"{new_x}"
				y_str = f"m{abs(new_y)}" if 0 > new_y else f"{new_y}"
				xy_list.append( (x_str, y_str) )
		self.xy_list = xy_list
		return xy_list

	def get_tile_xy_file_name_list(self, tile_dir = None, filename_list = [], batch_size = 0 ):
		"""
		revision: 20190801, 20190725
		0 == batch_size:
			read all files in tile_dir and then return all these files in a list containing tuples,
			each tuple is ( x, y, filename )
		0 < batch_size:
			return a dict containing such lists above-mentioned
		"""
		if tile_dir is None and isinstance( filename_list, list ) and 0 < len( filename_list ):
			# before and after sort, file_name_list will look like this:
			# ['12158_2387_16.png', '12159_2387_16.png', '12158_2386_16.png', '12157_2387_16.png', '12158_2388_16.png'... ]
			# ['12154_2386_16.png', '12154_2387_16.png', '12154_2388_16.png', '12154_2389_16.png', '12155_2386_16.png'... ]
			filename_list.sort( reverse=False )
		else:
			filename_list = os.listdir( tile_dir )
			# after testing, there is no need to run this on Windows, but Linux and mac have not been tested
			filename_list.sort( reverse=False )
		x_list = []
		y_list = []
		xy_list = []

		# process file names and process negative tile numbers(those starting with 'm')
		# however, in China there is no negative tile number!
		for filename in filename_list:
			filename_fragment = filename.split("_")
			x_str, y_str = filename_fragment[:2]
			if -1 == x_str.find("m"):
				x = int( x_str )
			else:
				x = -1 * int( x_str.strip("m") )

			if -1 == y_str.find("m"):
				y = int( y_str )
			else:
				y = -1 * int( y_str.strip("m") )

			x_list.append( x )
			y_list.append( y )
			xy_list.append( (x, y, filename) )

		min_x = abs(min( x_list ))
		min_y = abs(min( y_list ))
		has_negative_x = True if 0 > min( x_list ) else False
		has_negative_y = True if 0 > min( y_list ) else False
		new_xy_list = []
		new_x_list = []
		new_y_list = []
		for one_xy in xy_list:
			x, y, filename = one_xy
			new_x = (x + min_x) if has_negative_x else x
			new_y = (y + min_y) if has_negative_y else y
			new_xy_list.append( ( new_x, new_y, filename) )
			new_x_list.append( new_x )
			new_y_list.append( new_y )

		if 0 == batch_size:
			return new_xy_list

		new_x_list = list(set(new_x_list))
		new_y_list = list(set(new_y_list))
		new_x_list.sort()
		new_y_list.sort()

		return self.divide_xy_into_batches( xy_list = new_xy_list, x_list = new_x_list, y_list = new_y_list, batch_size = batch_size )

	def divide_xy_into_batches(self, xy_list = [], x_list = [], y_list = [], batch_size = 100 ):
		"""
		to return a dict containing all lists. The largest list shall be 101 X 101
		"""
		x_batches = math.ceil(len(x_list) / batch_size)
		x_batches = int( x_batches )
		y_batches = math.ceil(len(y_list) / batch_size)
		y_batches = int( y_batches )

		new_xy_dict = {}
		for x_i in range(x_batches):
			new_xy_dict[x_i] = {}

		min_x = min( x_list )
		min_y = min( y_list )
		for index, item_tuple in enumerate( xy_list ):
			x, y, filename = item_tuple
			x_ptr = math.floor( (x - min_x) / batch_size )
			y_ptr = math.floor( (y - min_y) / batch_size )
			this_batch = []

			if y_ptr in new_xy_dict[x_ptr].keys():
				this_batch = new_xy_dict[x_ptr][y_ptr]
			this_batch.append( item_tuple )
			new_xy_dict[x_ptr][y_ptr] = this_batch
		
		return new_xy_dict


	def stack_tiles(self, tile_dir = None, save_result = False, z = 4, batch_size = 0 ):
		"""
			numpy实现合并多维矩阵、list的扩展方法：https://www.php.cn/python-tutorials-395705.html
			batch_size > 0: will only stack batch_size X batch_size tiles each time to avoid memory overflow
			[
			(5, 6, '0_0_4.png'), (5, 7, '0_1_4.png'), (5, 8, '0_2_4.png'), (5, 9, '0_3_4.png'), (5, 10, '0_4_4.png'), (5, 5, '0_m1_4.png'), 
			(5, 4, '0_m2_4.png'), (5, 3, '0_m3_4.png'), (5, 2, '0_m4_4.png'), (5, 1, '0_m5_4.png'), (5, 0, '0_m6_4.png'), 
			(6, 6, '1_0_4.png'), (6, 7, '1_1_4.png'), (6, 8, '1_2_4.png'), (6, 9, '1_3_4.png'), (6, 10, '1_4_4.png'), (6, 5, '1_m1_4.png'), 
			(6, 4, '1_m2_4.png'), (6, 3, '1_m3_4.png'), (6, 2, '1_m4_4.png'), (6, 1, '1_m5_4.png'), (6, 0, '1_m6_4.png'), 
			(7, 6, '2_0_4.png'), (7, 7, '2_1_4.png'), (7, 8, '2_2_4.png'), (7, 9, '2_3_4.png'), (7, 10, '2_4_4.png'), (7, 5, '2_m1_4.png'), 
			(7, 4, '2_m2_4.png'), (7, 3, '2_m3_4.png'), (7, 2, '2_m4_4.png'), (7, 1, '2_m5_4.png'), (7, 0, '2_m6_4.png'), 
			(8, 6, '3_0_4.png'), (8, 7, '3_1_4.png'), (8, 8, '3_2_4.png'), (8, 9, '3_3_4.png'), (8, 10, '3_4_4.png'), (8, 5, '3_m1_4.png'), 
			(8, 4, '3_m2_4.png'), (8, 3, '3_m3_4.png'), (8, 2, '3_m4_4.png'), (8, 1, '3_m5_4.png'), (8, 0, '3_m6_4.png'), 
			(9, 6, '4_0_4.png'), (9, 7, '4_1_4.png'), (9, 8, '4_2_4.png'), (9, 9, '4_3_4.png'), (9, 10, '4_4_4.png'), (9, 5, '4_m1_4.png'), 
			(9, 4, '4_m2_4.png'), (9, 3, '4_m3_4.png'), (9, 2, '4_m4_4.png'), (9, 1, '4_m5_4.png'), (9, 0, '4_m6_4.png'), 
			(4, 6, 'm1_0_4.png'), (4, 7, 'm1_1_4.png'), (4, 8, 'm1_2_4.png'), (4, 9, 'm1_3_4.png'), (4, 10, 'm1_4_4.png'), (4, 5, 'm1_m1_4.png'), 
			(4, 4, 'm1_m2_4.png'), (4, 3, 'm1_m3_4.png'), (4, 2, 'm1_m4_4.png'), (4, 1, 'm1_m5_4.png'), (4, 0, 'm1_m6_4.png'), 
			(3, 6, 'm2_0_4.png'), (3, 7, 'm2_1_4.png'), (3, 8, 'm2_2_4.png'), (3, 9, 'm2_3_4.png'), (3, 10, 'm2_4_4.png'), (3, 5, 'm2_m1_4.png'), 
			(3, 4, 'm2_m2_4.png'), (3, 3, 'm2_m3_4.png'), (3, 2, 'm2_m4_4.png'), (3, 1, 'm2_m5_4.png'), (3, 0, 'm2_m6_4.png'), 
			(2, 6, 'm3_0_4.png'), (2, 7, 'm3_1_4.png'), (2, 8, 'm3_2_4.png'), (2, 9, 'm3_3_4.png'), (2, 10, 'm3_4_4.png'), (2, 5, 'm3_m1_4.png'), 
			(2, 4, 'm3_m2_4.png'), (2, 3, 'm3_m3_4.png'), (2, 2, 'm3_m4_4.png'), (2, 1, 'm3_m5_4.png'), (2, 0, 'm3_m6_4.png'), 
			(1, 6, 'm4_0_4.png'), (1, 7, 'm4_1_4.png'), (1, 8, 'm4_2_4.png'), (1, 9, 'm4_3_4.png'), (1, 10, 'm4_4_4.png'), (1, 5, 'm4_m1_4.png'), 
			(1, 4, 'm4_m2_4.png'), (1, 3, 'm4_m3_4.png'), (1, 2, 'm4_m4_4.png'), (1, 1, 'm4_m5_4.png'), (1, 0, 'm4_m6_4.png'), 
			(0, 6, 'm5_0_4.png'), (0, 7, 'm5_1_4.png'), (0, 8, 'm5_2_4.png'), (0, 9, 'm5_3_4.png'), (0, 10, 'm5_4_4.png'), (0, 5, 'm5_m1_4.png'), 
			(0, 4, 'm5_m2_4.png'), (0, 3, 'm5_m3_4.png'), (0, 2, 'm5_m4_4.png'), (0, 1, 'm5_m5_4.png'), (0, 0, 'm5_m6_4.png')
			]

			all_row_matrix takes 20.6251220703125 MB for Level 4 which has 110 files (243 kb); this png file has 2560 X 2816 (663 kb)
			all_row_matrix takes 468.7501220703125 MB for Level 17 which has 2500 files; this png file has 12800 X 12800 (53.4 MB)
			all_row_matrix takes 1875.0001220703125 MB (memory usage is identical) for Level 17 which has 10000 files; these png files have 
			25600 X 25600 (253 MB, 305 MB, 111 MB, 175 MB, 198 MB, 175 MB, 198 MB, 63.4 MB)
			all_row_matrix takes 675.0001220703125 MB (memory usage is identical) for Level 17 which has 3600 files; these png files have 
			25600 X 9216 (9.54 MB, 10.7 MB)
			all_row_matrix takes 787.5001220703125 MB (memory usage is identical) for Level 17 which has 3600 files; these png files have
			10752 X 25600 (111 MB, 77.6 MB, 14 MB)
		References:
			根据：百度与谷歌地图瓦片组织方式对比https://www.cnblogs.com/janehlp/archive/2012/08/27/2658106.html
		"""
		if tile_dir is None:
			tile_dir = self.crawled_dir

		if 0 == batch_size:
			new_xy_list = self.get_tile_xy_file_name_list( tile_dir = tile_dir, filename_list = [], batch_size = batch_size )
			batch_tuple = (0, 0)
			self.stack_one_batch( new_xy_list = new_xy_list, tile_dir = tile_dir, save_result = save_result, z = z, batch_tuple = batch_tuple, show_image = True )
		elif 0 < batch_size:
			new_xy_dict = self.get_tile_xy_file_name_list( tile_dir = tile_dir, filename_list = [], batch_size = batch_size )
			for index_x, key_x in enumerate( new_xy_dict ):
				for index_y, key_y in enumerate( new_xy_dict[key_x] ):
					new_xy_list = new_xy_dict[key_x][key_y]
					batch_tuple = (key_x, key_y)
					self.stack_one_batch( new_xy_list = new_xy_list, tile_dir = tile_dir, save_result = save_result, z = z, batch_tuple = batch_tuple, show_image = True )
		else:
			return False

		cv2.waitKey(0)
		cv2.destroyAllWindows()

	def stack_one_batch(self, new_xy_list = [], tile_dir = None, save_result = False, z = 4, batch_tuple = (), show_image = False ):
		"""
		revision: 20190801, 20190725
		Usage:
			whole_image = self.stack_one_batch( new_xy_list = new_xy_list, tile_dir = tile_dir, save_result = save_result, z = z, batch_tuple = batch_tuple, show_image = False )
			new_xy_list is a list containing tuples; each tuple looks like: ( x, y, filename )
			For production, set show_image = False. Our cluster runs on Linux without any graphy GUI
		"""
		tile_matrix_dict = {}
		for one_tuple in new_xy_list:
			x, y, filename = one_tuple
			file_path = os.path.join( tile_dir, filename )
			if y not in tile_matrix_dict.keys():
				tile_matrix_dict[y] = {}
			tile_matrix_dict[y][x] = cv2.imread( file_path )

		# 因为python的字典采用hash存储；无法反序输入，只好用下面方法
		y_keys = list( tile_matrix_dict.keys() )
		y_keys.sort(reverse = True)

		all_row_matrix = None
		for index_y, row_y in enumerate( y_keys ):
			this_row = tile_matrix_dict[row_y]
			this_row_matrix = None
			for index_x, col_x in enumerate( this_row ):
				if this_row_matrix is None:
					this_row_matrix = this_row[col_x]
				else:
					this_row_matrix = np.concatenate((this_row_matrix, this_row[col_x]), axis = 1) # axis == 1表示按行合并；0表示按列合并
			if all_row_matrix is None:
				all_row_matrix = this_row_matrix
			else:
				all_row_matrix = np.concatenate( (all_row_matrix, this_row_matrix), axis = 0)
		self.write_log( f"all_row_matrix takes {sys.getsizeof(all_row_matrix)/1048576} MB" )
		batch_x, batch_y = batch_tuple
		if show_image: cv2.imshow( f"x{batch_x}y{batch_y}", all_row_matrix )
		if save_result:
			this_file_path = os.path.join( tile_dir, "..", f"level{z}_x{batch_x}_y{batch_y}.png" )
			cv2.imwrite( this_file_path, all_row_matrix )
		return all_row_matrix

	def get_xy_box(self, data_file_name = "yueyang2km_yueyanglouqu_with_zero.txt", add_delta= True, edge = 3.2 ):
		"""
			copied from easygo/input
			广州市行政区划四至：{'min_lat': 22.52969, 'max_lat': 23.92969, 'min_lng': 112.983874, 'max_lng': 114.063874}，其中114.063874,23.92969所在的瓦片是：
			https://gss0.bdstatic.com/8bo_dTSlRMgBo1vgoIiO_jowehsv/tile/?qt=vtile&x=24800&y=5326&z=17&styles=pl&scaler=1&udt=20190723
			而112.983874,22.52969所在的瓦片是：
			https://gss0.bdstatic.com/8bo_dTSlRcgBo1vgoIiO_jowehsv/tile/?qt=vtile&x=24565&y=4997&z=17&styles=pl&scaler=1&udt=20190723
			因此广州的四至瓦片编号是：(24800, 5326), (24565, 4997)；考虑到这些经纬度是2km X 2km；还需要向外扩大3个瓦片（每一片瓦片大约400米）编号。就是：
			(24803, 5329), (24562, 4994)

			20190726发现应该是16级的瓦片，因此广州四至（已经外延了3个编号）16级瓦片编号是：(12403, 2666), (12279, 2495)
			https://gss0.bdstatic.com/8bo_dTSlRsgBo1vgoIiO_jowehsv/tile/?qt=vtile&x=12400&y=2663&z=16&styles=pl&scaler=1&udt=20190723
			https://gss0.bdstatic.com/8bo_dTSlR1gBo1vgoIiO_jowehsv/tile/?qt=vtile&x=12282&y=2498&z=16&styles=pl&scaler=1&udt=20190723
		"""
		file_path = os.path.join( self.root_path, self.input_folder_name, data_file_name )
		center = []
		try:
			df = pandas.read_csv( file_path )
			for index, row in df.iterrows():
				center.append( "%.6f,%.5f" % (float(row['x']), float(row['y'])) )
		except Exception as ex:
			self.write_log( f"Exception happened while reading file. Exception = {ex}" )
			return None
		min_lng = 360
		max_lng = 0
		min_lat = 91
		max_lat = 0
		for one in center:
			xy_list = one.split(",")
			if 1 < len( xy_list ):
				try:
					x = float( xy_list[0] )
					y = float( xy_list[1] )
				except Exception as ex:
					self.write_log( f"ValueException. Exception = {ex}; xy_list = {xy_list}" )
				else:
					if x < min_lng:
						min_lng = x
					if x > max_lng:
						max_lng = x
					if y < min_lat:
						min_lat = y
					if y > max_lat:
						max_lat = y
		return_dict = {
			"min_lat": min_lat,
			"max_lat": max_lat,
			"min_lng": min_lng,
			"max_lng": max_lng,
		}
		if add_delta and 0 < edge:
			lng_delta = 0.01167 * edge
			lat_delta = 0.009009009 * edge
			return_dict["min_lat"] -= lat_delta
			return_dict["max_lat"] += lat_delta
			return_dict["min_lng"] -= lng_delta
			return_dict["max_lng"] += lng_delta
		return return_dict

	def find_image_in_the_whole( self, whole_image = None, template = None, save_result = False, result_file_path = "", show_result = False, show_window = "marked result image" ):
		"""
		Description:
			to find template from full_image
		revision: 20190801
		"""
		method = "cv2.TM_CCOEFF"
		top_left = (-1, -1)
		bottom_right = (-1, -1)
		img = None
		now_ts = time.time()
		try:
			h, w = template.shape[:2]
			img = whole_image.copy()
			res = cv2.matchTemplate(whole_image, template, eval(method) )
			min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
			top_left = max_loc
			bottom_right = (top_left[0] + w, top_left[1] + h)
			# self.write_log( f"top_left = {top_left} bottom_right = {bottom_right}" )
			# top_left = (813, 376) bottom_right = (826, 394) # larger y at bottom; smaller y on top
			if save_result:
				cv2.rectangle(img, top_left, bottom_right, 255, 20)
				cv2.imwrite( result_file_path, img )
			if show_result: cv2.imshow(show_window, img )
		except Exception as ex:
			error_msg = f"Cannot find image from whole_image. Exception ({ex})"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		end_ts = time.time()
		return top_left, bottom_right, img, (end_ts - now_ts)

	def match_known_xy_pts( self, full_map_path = None, known_xy_dir = None ):
		"""
		revision: 20190801, 20190724
		modified from Method test_match_template3 of Class ExtractHeatmapData
		"""
		if known_xy_dir is None:
			known_xy_dir = os.path.join( self.root_path, self.input_folder_name )

		try:
			now_ts = time.time()
			whole_image = cv2.imread( full_map_path )
			end_ts = time.time()
			self.write_log( f"totally {end_ts - now_ts} seconds are taken for reading the full map ({full_map_path})" )
			# for a 300 MB map (in png file), it takes 9 minutes to read on Entrobus 32.
		except Exception as ex:
			self.write_log( f"cannot read {full_map_path}. Exception = {ex}" )
			return False

		show_result = False
		for one_file_name in os.listdir( known_xy_dir ):
			if -1 == one_file_name.find(".png"):
				continue
			this_file_path = os.path.join( known_xy_dir, one_file_name )
			result_file_name = one_file_name.replace(".png", "___TM_CCOEFF.png")
			result_file_path = os.path.join( known_xy_dir, result_file_name )
			now_ts = time.time()
			template = cv2.imread( this_file_path )
			end_ts = time.time()
			top_left, bottom_right, img, seconds = self.find_image_in_the_whole( whole_image = whole_image, template = template, save_result = True, result_file_path = result_file_path, show_result = show_result, show_window = result_file_name )
			self.write_log( f"{end_ts - now_ts + seconds} seconds are taken. top_left = {top_left}, bottom_right = {bottom_right}" )

		if show_result:	cv2.waitKey(0)

	def scale_templates(self, template_dir = None, scale = 1.286):
		if not os.path.isdir(template_dir):
			self.write_log( f"{template_dir} does not exist" )
			return False
		if 0 >= scale:
			self.write_log( f"Error: {scale} <= 0" )
			return False

		for template in os.listdir(template_dir):
			if -1 == template.find(".png"):
				continue
			# try:
			# 	pass
			# except Exception as ex:
			# 	raise ex
			template_image = cv2.imread( os.path.join( template_dir, template ) )
			result = cv2.resize(template_image, None, fx = scale, fy = scale, interpolation = cv2.INTER_CUBIC)
			# height, width = template_image.shape[:2]
			# result = cv2.resize( template_image, ( scale*width, scale*height ), interpolation = cv2.INTER_CUBIC)
			new_file_name = template.replace(".png", f"___scaled{scale}.png")
			cv2.imwrite( os.path.join( template_dir, new_file_name ), result )
			self.write_log( f"{new_file_name} is wrriten" )

	def test(self):
		mapping_dict = {
			'111.838095,21.578807': {'tile_x_number': 12158, 'tile_y_number': 2387, 'x_from_left_in_this_tile': 25, 'y_from_bottom_in_this_tile': 221, 'lng': 111.838095, 'lat': 21.578807}, 
			'114.706195,23.740876': {'tile_x_number': 6234, 'tile_y_number': 1320, 'x_from_left_in_this_tile': 242, 'y_from_bottom_in_this_tile': 143, 'lng': 114.706195, 'lat': 23.740876},
		}
		two_point_list, x_ratio, y_ratio = self.calculate_tile_lng_lat( mapping_dict = mapping_dict )
		print( two_point_list, x_ratio, y_ratio )

		# {'tile_x_number': 12158, 'tile_y_number': 2387, 'x_from_left_in_this_tile': 25, 'y_from_bottom_in_this_tile': 221, 'lng': 111.838095, 'lat': 21.578807} 
		# {'tile_x_number': 6234, 'tile_y_number': 1320, 'x_from_left_in_this_tile': 242, 'y_from_bottom_in_this_tile': 143, 'lng': 114.706195, 'lat': 23.740876}
		# {'left_lng': 111.83804771303616, 'bottom_lat': 21.577058226991912, 'tile_x_number': 12158, 'tile_y_number': 2387} 
		# {'left_lng': 114.70573726219014, 'bottom_lat': 23.739744440994766, 'tile_x_number': 6234, 'tile_y_number': 1320}
		# [{'left_lng': 111.83804771303616, 'bottom_lat': 21.577058226991912, 'tile_x_number': 12158, 'tile_y_number': 2387}, 
		# {'left_lng': 114.70573726219014, 'bottom_lat': 23.739744440994766, 'tile_x_number': 6234, 'tile_y_number': 1320}] 
		# 1.891478553108926e-06 7.913000036599198e-06

if __name__ == "__main__":
	# Level 17
	# xy_list = [
	# 	(24562, 4994),
	# 	(24803, 5329),
	# ]

	# Level 16
	xy_list = [
		(12403, 2666),
		(12279, 2495),
	]
	# app = Bmapm1Spider( xy_list = [], four_edge_xy_list = xy_list )
	# app.request_and_save( 16 )

	# for getting all tiles at Level 4
	# app = BaidumaptileSpider( xy_list = [], four_edge_xy_list = [] )
	# app.request_and_save(4)

	# for stacking all tiles
	# app = BaidumaptileSpider( xy_list = [], four_edge_xy_list = [] )
	# self.write_log( isinstance( app, Mapping ) )
	# self.write_log( '\n'.join([ "%s:%s" % item for item in app.__dict__.items()]) )
	# tile_dir = os.path.join( app.root_path, app.output_folder_name, "level4_20190718" )
	# app.stack_tiles( tile_dir = None, save_result = True, z = 16, batch_size = 0 )
	# tile_dir = os.path.join( app.root_path, app.output_folder_name, "level17_guangzhou_20190718" )
	# app.stack_tiles( tile_dir = tile_dir, save_result = True, z = 17, batch_size = 100 )

	# get min_lat, max_lat, min_lng, max_lng of a city
	# app = BaidumaptileSpider( xy_list = [], four_edge_xy_list = [] )
	# gz_dict = app.get_xy_box( data_file_name = "guangzhou2km_with_zero.txt", add_delta = False )
	# self.write_log( gz_dict )

	# app = BaidumaptileSpider( xy_list = [], four_edge_xy_list = [] )
	# full_map_path = os.path.join( app.root_path, app.output_folder_name, "level16_x0_y0.png" ) # "level17_x0_y1cut.png"
	# app.match_known_xy_pts( full_map_path = full_map_path )
	# level17_x0_y1cut.png has about 4000 X 4000 pixels; if 16 X 16 tiles are used, one single map file would be 4096 X 4096 pixels and about 7 MB.

	# app = Bmapm1Spider( xy_list = [], four_edge_xy_list = [] )
	# full_map_path = os.path.join( app.root_path, "112.992911___22.536984.png" )
	# app.match_known_xy_pts( full_map_path = full_map_path )

	# app = BaidumaptileSpider( xy_list = [], four_edge_xy_list = [] )
	# app.scale_templates( template_dir = os.path.join(app.root_path, app.input_folder_name) )

	app = Bmapm1Spider( xy_list = [], four_edge_xy_list = [] )
	# app.test()
	app.webdriver_operation(url = "http://api.map.baidu.com/lbsapi/getpoint/index.html")
	# app.webdriver_operation_debug( url = "http://quotes.toscrape.com/page/2/" )
	# app.debug_locator()

	xy_list = [
		(113, 23),				# x3071y638z14		x24568y5107z17
		(111.838095,21.578807), # x3039y596z14		x24316y4775z17
		(114.706195,23.740876), # x3117y660z14		x24939y5282z17
		(112.123244,23.411807), # x3047y650z14		x24378y5204z17
	]
	for one_xy in xy_list:
		x, y = one_xy
		# x, y = app.transfer_lng_lat(lng = x, lat = y)
		# self.write_log( f"Level 17: x = {x}; y = {y}" )
