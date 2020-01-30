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
import shutil
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

from house163.settings import settings

sys.path.append("..")
from library.commonmethodclass import CommonMethodClass

class House163Spider(object):
	"""
	爬取网易房产。uri类似：
	http://data.house.163.com/gz/housing/trend/product/todayflat/180/day/allproduct/1.html?productname=天河星作,广州龙湖·双珑原著,时代天韵·星御,越秀星汇云城
	http://data.house.163.com/gz/housing/trend/product/todayflat/180/day/allproduct/1.html?productname=时代云图（广州）
	上述url在webdriver地址栏内不需要urlencode

	todo：在这里增加一个方法来下载这个页面全国的数据
	20190810收到王总其他页面数据在下面uri中，现在只有广州市手工下载即可
	http://data.house.163.com/gzxf/district/trend.html?datenum=360&startDate=&endDate=&district=&trend=1
	http://data.house.163.com/gzxf/district/trend.html?datenum=360&startDate=&endDate=&district=天河&trend=1
	天河  海珠  越秀  荔湾  白云  黄埔  番禺  花都  南沙  增城  从化
	"""
	name = "house163"

	now = None
	today = None
	settings = None
	root_path = None
	log_dir = None
	main_log_file_path = None
	debug = False
	crawled_dir = None
	csv_path = None
	excel_dir = None
	output_folder_name = None
	input_folder_name = None
	base_uri = None
	browser = None
	missed_url_file_name = ""
	downloaded_log_file_path = ""

	wait_time = None
	implicitly_wait_time = 30
	min_wait_time = 0.1
	wait_time_step = 1.0
	maximal_wait_time = 900 # 900 seconds == 15 minutes
	maximal_requests = None

	key_list = [
		"日期", "已售套数","已售面积","已售均价","已售销售金额","累计已售套数", "累计已售面积", "累计未售套数", "累计未售面积", "退房次数",
	]

	def __init__(self ):
		"""
		revision 20190810
		"""
		self.init_self_attributes( )

	def init_self_attributes(self):
		"""
		revision 20190810
		"""
		self.now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		self.today = datetime.datetime.now().strftime("%Y%m%d")
		self.settings = settings
		self.root_path = self.settings.get( name="PROJECT_PATH", default="" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )
		self.main_log_file_path = os.path.join( self.log_dir, self.settings.get( name="MAIN_LOG_FILE_NAME", default="" ) )
		self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		self.crawled_dir = self.settings.get( name="CRAWLED_DIR", default = "" )
		self.csv_path = os.path.join(self.crawled_dir, f"house163_{self.today}.csv")
		self.excel_dir = self.settings.get( name="EXCEL_DIR", default = "" )
		self.output_folder_name = self.settings.get( name = "OUTPUT_FOLDER_NAME", default="" )
		self.input_folder_name = self.settings.get( name = "INPUT_FOLDER_NAME", default="" )
		self.base_uri = self.settings.get( name = "BASE_URI", default="" )
		self.browser = self.settings.get( name = "BROWSER", default="" )

		self.wait_time = 2 if self.debug else 3
		self.maximal_requests = self.settings.get( name = "MAXIMAL_REQUESTS", default=50 )
		self.missed_url_file_name = self.settings.get( name = "MISSED_URL_FILE_NAME", default="" )

		self.downloaded_log_file_path = os.path.join( self.log_dir, f"downloaded_file_{self.today}.log")

	def read_community_names(self):
		"""
		revision 20190810
		"""
		name_list = []
		district_list = []
		excel_file_path = os.path.join( self.root_path, self.input_folder_name, "163data20190810_801.xls" )
		excel_file_list = [ excel_file_path ]
		excel_file_path = os.path.join( self.root_path, self.input_folder_name, "163data20190810_701.xls" )
		excel_file_list.append( excel_file_path )
		try:
			for file_path in excel_file_list:
				excel_wordbook_dict = CommonMethodClass.read_excel_file( excel_file_path = file_path, log_file_path = self.main_log_file_path )
				row_list = excel_wordbook_dict["网易数据中心查询"]
				for row in row_list:
					if row[0] not in ["名称", "合计", "--"]:
						name_list.append( row[0] )
						district_list.append( row[1] )
		except Exception as ex:
			error_msg = f"Fail to read community names from excel files ({excel_file_list}) Exception = {ex}"
			CommonMethodClass.write_log( content = f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}", log_file_path = self.main_log_file_path )
		return name_list, district_list

	def read_one_community( self, excel_file_path = "" ):
		"""
		revision 20190810
		"""
		excel_file_list = [excel_file_path]
		date_list = []
		try:
			excluded_values = ["日期", "合计", ""]
			for file_path in excel_file_list:
				excel_wordbook_dict = CommonMethodClass.read_excel_file( excel_file_path = file_path, log_file_path = self.main_log_file_path )
				row_list = excel_wordbook_dict["Trade"]
				for row in row_list:
					if row[0] not in excluded_values and row[1] not in excluded_values:
						date_list.append( row[1:] )
		except Exception as ex:
			error_msg = f"Fail to read trade data from excel files ({excel_file_list}) Exception = {ex}"
			CommonMethodClass.write_log( content = f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}", log_file_path = self.main_log_file_path )
		return date_list

	def do_requests(self, community_name_list = [], district_list = [] ):
		"""
		revision: 20190810
		references:
			Selenium 如何使用webdriver下载文件（chrome浏览器）https://blog.csdn.net/weixin_41812940/article/details/82423892
			selenium WebDriver处理文件下载：https://www.cnblogs.com/111testing/p/6384553.html
			https://blog.csdn.net/it_blog/article/details/45340063
		"""
		error_msg = ""
		city = "广州"
		
		download_btn_xpath = "//div[@class='dc_homepage']/div[@class='dc_homepage_con clearfix']/div[@class='dc_homepage_right']/div[@class='ward']/a"
		temp_dir = os.path.join(self.excel_dir, "temporary")
		to_dir = os.path.join(self.excel_dir, "downloaded")
		if not os.path.isdir(temp_dir): os.makedirs( temp_dir )
		if not os.path.isdir(to_dir): os.makedirs( to_dir )
		header_dict = CommonMethodClass.get_headers(browser = self.browser, cookies = None, referer = None)
		
		try:
			chrome_options = Options()
			prefs = {
				"download.default_directory": temp_dir,
				"download.prompt_for_download": False,
			}
			chrome_options.add_experimental_option("prefs", prefs)
			chrome_options.add_argument( f"accept={header_dict['Accept']}" )
			chrome_options.add_argument( f"referer={header_dict['Referer']}" )
			chrome_options.add_argument( f"user-agent={header_dict['User-Agent']}" )
			chrome_options.add_argument( f"lang={header_dict['Accept-Language']}" )
			# chrome_options.add_argument('--headless') # 在广州分公司将无头配置项注销掉，直接在windows下运行
			chrome_driver = webdriver.Chrome( options=chrome_options, executable_path="chromedriver.exe" ) # 先将chromedriver.exe放置在PATH内
			chrome_driver.implicitly_wait( self.implicitly_wait_time )
			chrome_driver.maximize_window()

			log_file_path = os.path.join( self.log_dir, self.missed_url_file_name )
			for index, community_name in enumerate(community_name_list):
				one_url = f"{self.base_uri}?productname={community_name}"
				requested_counter = 0
				while True:
					requested_counter += 1 
					if requested_counter > self.maximal_requests:
						error_msg = f"totally {self.maximal_requests} requests have been sent for {one_url}; giving up..."
						CommonMethodClass.write_log( content = f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}", log_file_path = self.main_log_file_path )
						break
					chrome_driver.get( one_url )
					CommonMethodClass.write_log( content = f"requesting {one_url}", log_file_path = self.main_log_file_path )
					chrome_driver.implicitly_wait( self.implicitly_wait_time )

					element = CommonMethodClass.get_element( webdriver = chrome_driver, xpath = download_btn_xpath, elements_bool = False, use_id = False, debug = self.debug, log_file_path = self.main_log_file_path )

					if element is None:
						sleep( self.min_wait_time + random.random() * self.wait_time_step )
						continue
					element.click()
					chrome_driver.implicitly_wait( self.implicitly_wait_time )

					# 监听temp_dir目录
					download_counter = 0
					next_community = False
					while True:
						latest_file_path, latest_file_name, latest_create_ts, fsize = CommonMethodClass.get_file_info( file_dir = temp_dir, to_dir = to_dir, endswith = ".xls" )
						if 0 < fsize:
							break
						if 5 < download_counter:
							error_msg = f"totally {download_counter} file checks have been conducted for index {index} ({community_name}) at {one_url}; but no downloaded file received; giving up..."
							CommonMethodClass.write_log( content = f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}", log_file_path = self.main_log_file_path )
							next_community = True
							break
						download_counter += 1
						sleep(5)
					if next_community:
						break

					# copy to self.excel_dir with new file name
					dst_file_path = os.path.join( self.excel_dir, f"community{index}.xls" )
					shutil.copyfile( latest_file_path, dst_file_path )
					content = f"{index}, {community_name}, {dst_file_path}, {latest_file_path}"
					CommonMethodClass.write_log( content = content, log_file_path = self.downloaded_log_file_path )

					# 将excel文件解析处理并写csv文件
					city_str = f"{city}___{district_list[index]}" if index < len(district_list) else f"{city}___unknown"
					self.append_one_excel_file_to_csv( excel_file_path = dst_file_path, community_name = community_name, url = one_url, city = city_str )

					# jump out this loop to request next one_url
					break
				if self.debug: break
			CommonMethodClass.cleanup_webdriver( webdriver = chrome_driver )	
		except NoSuchElementException as ex:
			error_msg = f"NoSuchElementException happended while operating webdriver. NoSuchElementException = {ex}"
		except Exception as ex:
			error_msg = f"Exception happended while operating webdriver. Exception = {ex}"
		
		if 0 < len( error_msg ):
			CommonMethodClass.write_log( content = f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}", log_file_path = self.main_log_file_path )
			CommonMethodClass.cleanup_webdriver( webdriver = chrome_driver )
			return 0
		return requested_counter

	def append_one_excel_file_to_csv(self, excel_file_path = "", community_name = "", url = "", city = ""):
		"""
		revision 20190810
		"""
		date_list = self.read_one_community( excel_file_path = excel_file_path)
		temp_list = [self.key_list]
		temp_list.extend( date_list )
		date_list = temp_list
		community_dict = {
			"community": community_name,
			"half_year": date_list,
		}
		CommonMethodClass.load_item_and_write_csv( info_list = [community_dict], url = url, city = city, csv_file_path_str = self.csv_path, log_file_path = self.main_log_file_path )

	def execute(self):
		"""
		revision 20190810
		"""
		name_list, district_list = self.read_community_names()
		if 0 < len( name_list ): self.do_requests( community_name_list = name_list, district_list = district_list )

	def test(self):
		name_list, district_list = self.read_community_names()
		print( len(name_list), len( district_list ), district_list )
		# if 0 < len( name_list ): self.do_requests( community_name_list = name_list )
		# excel_file_path = os.path.join( self.excel_dir, "community0.xls" )
		# community_name = "天河星作"
		# date_list = self.read_one_community( excel_file_path = excel_file_path)
		# temp_list = [self.key_list]
		# temp_list.extend( date_list )
		# date_list = temp_list
		
		# city = "广州___增城"
		# one_url = "http://data.house.163.com/gz/housing/trend/product/todayflat/180/day/allproduct/1.html?productname=天河星作"
		# community_dict = {
		# 	"community": community_name,
		# 	"half_year": date_list,
		# }
		# CommonMethodClass.load_item_and_write_csv( info_list = [community_dict], url = one_url, city = city, csv_file_path_str = self.csv_path, log_file_path = self.main_log_file_path )

if __name__=='__main__':
	app = House163Spider( )
	# app.test()
	app.execute()
