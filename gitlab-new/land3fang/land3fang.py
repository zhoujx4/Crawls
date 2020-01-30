import fitz
import datetime
import time
from time import sleep
import re
import os
import sys
import csv
import socket
import random
from urllib import parse
from collections.abc import Iterable
from collections.abc import Mapping
from PIL import Image

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

from land3fang.settings import settings

class Land3fangSpider(object):
	"""
	由于采用scrapy爬取需要登录的lang.3fang.com页面有困难，这里增加这个补充爬虫
	"""
	name = "land3fang"

	now = None
	today = None
	settings = None
	root_path = None
	log_dir = None
	debug = False
	crawled_dir = None
	html_dir = None
	output_folder_name = None
	input_folder_name = None
	locator_png_file_name = None
	base_uri = None
	browser = None
	csv_file_path = None
	wait_time = None

	def __init__(self ):
		self.init_self_attributes( )

	def init_self_attributes(self):
		self.now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		self.today = datetime.datetime.now().strftime("%Y%m%d")
		self.settings = settings
		self.root_path = self.settings.get( name="PROJECT_PATH", default="" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )
		self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		self.crawled_dir = self.settings.get( name="CRAWLED_DIR", default = "" )
		self.html_dir = self.settings.get( name="HTML_DIR", default = "" )
		self.output_folder_name = self.settings.get( name = "OUTPUT_FOLDER_NAME", default="" )
		self.input_folder_name = self.settings.get( name = "INPUT_FOLDER_NAME", default="" )
		self.browser = self.settings.get( name = "BROWSER", default="" )
		self.csv_file_path = os.path.join( self.crawled_dir, f"makeup_{self.today}.csv" )
		self.wait_time = 3 if self.debug else 60

	def write_log(self, content = None, logfilename = None, content_only = False):
		if isinstance(content, Iterable) and 0 < len( content ):
			today = datetime.datetime.now().strftime("%Y%m%d")
			if logfilename is None:
				logfilename = f"{self.name}{today}.log"
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

	def load_item_and_write_csv(self, info_dict = {}, url = "", city = "", requested_counter = 0):
		info_dict["city"] = city
		info_dict["url"] = url
		info_dict["server"] = socket.gethostname()
		info_dict["date"] = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		self.append_row( key_list = info_dict.keys(), item_list = info_dict.values(), csv_file_path_str = self.csv_file_path )
		return requested_counter + 1

	def do_makeup_requests(self, url_list = []):
		"""
		revision: 20190807
		将登录以后的webdriver对象返回
		"""
		if type( url_list ) not in [list] or 1 > len( url_list ):
			return 0
		
		error_msg = ""
		header_dict = self.get_headers(self.browser)
		requested_counter = 0
		try:
			chrome_options = Options()
			chrome_options.add_argument( f"accept={header_dict['Accept']}" )
			chrome_options.add_argument( f"referer={header_dict['Referer']}" )
			chrome_options.add_argument( f"user-agent={header_dict['User-Agent']}" )
			chrome_options.add_argument( f"lang={header_dict['Accept-Language']}" )
			# chrome_options.add_argument('--headless') # 在广州分公司将无头配置项注销掉，直接在windows下运行
			chrome_driver = webdriver.Chrome( options=chrome_options, executable_path="chromedriver.exe" ) # 先将chromedriver.exe放置在PATH内
			chrome_driver.implicitly_wait(30)
			chrome_driver.maximize_window()

			while True:
				chrome_driver.get( url_list[0]["url"] )
				sleep( self.wait_time ) # 等待1分钟来登录；在这里收到输入手机号码和验证码、关闭登录页面、并刷新原来的浏览器页面
				info_dict = self.parse_detailed_response_field( webdriver = chrome_driver )
				if type( info_dict ) in [dict ] and "土地交易信息" in info_dict.keys():
					row2str = info_dict["土地交易信息"][2]
					print( row2str )
					if -1 < row2str.find("******"):
						continue
					else:
						# 已经登录了，现在字段数据内没有******了
						if 0 < len( info_dict ):
							requested_counter = self.load_item_and_write_csv( info_dict = info_dict, url = url_list[0]["url"], city = url_list[0]["city"], requested_counter = requested_counter )
							self.save_html( body = chrome_driver.page_source, url = url_list[0]["url"] )
							break
						else:
							self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, wrong info_dict: {info_dict}" )
				else:
					error_msg = f"wrong info_dict = {info_dict}"
					self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
					continue # 经常出现502页面
				
		except NoSuchElementException as ex:
			error_msg = f"NoSuchElementException happended while operating webdriver. NoSuchElementException = {ex}"
		except Exception as ex:
			error_msg = f"Exception happended while operating webdriver. Exception = {ex}"
		
		if 0 < len( error_msg ):
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			self.cleanup_webdriver( webdriver = chrome_driver )
			return 0

		# 爬取第2到100条记录。每一个账号每天只可以爬取100条
		if 1 < len( url_list ):
			no_such_element = False
			for index, url_dict in enumerate( url_list ):
				if 0 == index:
					continue
				while True:
					if no_such_element:
						chrome_driver.refresh() # refresh比get更加好
					else:
						chrome_driver.get( url_dict["url"] )
					no_such_element = False
					error_msg = ""
					sleep( random.randint(3,10) ) # 等待3到10秒钟
					try:
						info_dict = self.parse_detailed_response_field( webdriver = chrome_driver )
						print( info_dict )
						if 0 < len( info_dict ):
							requested_counter = self.load_item_and_write_csv( info_dict = info_dict, url = url_dict["url"], city = url_dict["city"], requested_counter = requested_counter )
							self.save_html( body = chrome_driver.page_source, url = url_dict["url"] )
							break
						else:
							self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, wrong info_dict: {info_dict}" )
					except NoSuchElementException as ex:
						error_msg = f"NoSuchElementException happended while operating webdriver. NoSuchElementException = {ex}"  # 经常出现502页面
						# Message: no such element: Unable to locate element: {"method":"xpath","selector":"//div[@id='printData1']"}
						no_such_element = True
					except Exception as ex:
						error_msg = f"Exception happended while operating webdriver. Exception = {ex}"

					if 0 < len( error_msg ):
						self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		self.cleanup_webdriver( webdriver = chrome_driver )
		return requested_counter

	def cleanup_webdriver(self, webdriver = None):
		try:
			webdriver.quit()
			webdriver.close()
		except Exception:
			pass

	def save_html( self, body = None, url = "" ):
		"""
		https://land.3fang.com/market/8bf37401-2bf7-4533-ab65-30eb70c3430d.html
		type(body) == str
		"""
		url_object = parse.urlparse( url )
		url_list = url_object.path.split("/")
		for one in url_list:
			if -1 < one.find(".html"):
				break
		html_file_path = os.path.join( self.html_dir, one )
		if type( body ) not in [bytes, str]:
			error_msg = f"type ({ type( body ) }) of body is NOT correct"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return False

		try:
			if type(body) in [str]:
				with open( html_file_path, "a", encoding = "utf-8" ) as f:
					f.write( body )
			elif type(body) in [bytes]:
				with open( html_file_path, "wb" ) as f:
					f.write( body )
		except Exception as ex:
			error_msg = f"fail to write body into {html_file_path} after requesting {url}. Exception = {ex}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return False
		return True

	def parse_detailed_response_field(self, webdriver = None ):
		text = {}
		if webdriver is None:
			return text

		information_div = webdriver.find_element_by_xpath( "//div[@id='printData1']" )

		title = information_div.find_element_by_xpath("./div[@class='tit_box01']").text
		land_id = information_div.find_element_by_xpath("./div[@class='menubox01 mt20']/span[@class='gray2']").text
		province_city_list = information_div.find_elements_by_xpath("./div[@class='menubox01 p0515']/div[@class='fl']")
		province_city = []
		for one in province_city_list:
			province_city.append( one.text )
		province_city = "___".join( province_city )

		if 0 < len( title ): text["title"] = title
		if 0 < len( land_id ): text["land_id"] = land_id
		if 0 < len( province_city ): text["province_city"] = province_city

		key2 = information_div.find_element_by_xpath("./div[@class='p1015']/div[@class='tit_box02 border03 mt20']").text
		if "土地交易信息" == key2:
			trade_info = {}
			tr_list2 = information_div.find_elements_by_xpath("./div[@class='p1015']/div[@class='tit_box02 border03 mt20']/following-sibling::div[@class='banbox']/table[@class='tablebox02 mt10']/tbody/tr")
			for index, one_tr in enumerate(tr_list2):
				td_list = one_tr.find_elements_by_xpath("./td")
				value_list = []
				for one_td in td_list:
					value_list.append( one_td.text )
				trade_info[index] = "___".join( value_list )
			text[key2] = trade_info

		return text
	
	def read_input_file(self):
		"""
		revision: 20190807
		读取数据清洗以后的文件
		"""
		finished_filename = "makeup_20190807.csv"
		finished_file_path = os.path.join( self.root_path, self.output_folder_name, "20190807", finished_filename )
		all_id_list = []
		try:
			with open( finished_file_path, newline="", encoding="utf-8" ) as csvfile:
				file_reader = csv.reader(csvfile) # , delimiter=' ', quotechar='|'
				for row in file_reader:
					if row[1] not in ["land_id"]: all_id_list.append( row[1] )
		except Exception as ex:
			error_msg = f"cannot read csv file, Exception = {ex}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return []

		english_city_name = {
			"佛山": "foshan",
			"广州": "guangzhou",
		}
		filename = "tudi_201808.csv"
		csv_file_path = os.path.join( self.root_path, self.input_folder_name, filename )
		return_list = []

		url_list = []
		city_list = []
		try:
			with open( csv_file_path, newline="", encoding="utf-8" ) as csvfile:
				file_reader = csv.reader(csvfile) # , delimiter=' ', quotechar='|'
				for row in file_reader:
					if -1 < row[8].find("https:") and row[1] not in all_id_list:
						this_link_dict = {}
						this_link_dict["city"] = english_city_name[ row[13] ]
						this_link_dict["url"] = row[8]
						return_list.append( this_link_dict )
		except Exception as ex:
			error_msg = f"cannot read csv file, Exception = {ex}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return []
		return return_list
	
	def execute(self):
		if self.debug:
			url_list = [{
				"url": "https://land.3fang.com/market/e5a24a64-2ece-43d6-97c4-33714695307d.html",
				"city": "guangzhou",
			}]
		else:
			url_list = self.read_input_file( )
		if 0 < len( url_list ):
			counter = self.do_makeup_requests( url_list )
			self.write_log( f"At {self.now}, {counter} requests have been sent" )
	
if __name__=='__main__':
	app = Land3fangSpider( )
	app.execute()
