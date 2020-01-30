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

from landchina.settings import settings

sys.path.append("..")
from library.commonmethodclass import CommonMethodClass

class LandchinaSpider(object):
	"""
	爬取https://www.landchina.com/default.aspx?tabid=263页面
	备注：
	1、20190808采用chrome webdriver爬取失败（失败的现象是在webdriver驱动的
	浏览器内可以输入“广东省”等关键词；但是点击“查询”以后加载1秒钟以后就终止
	加载了。）
	2、20190812采用scrapy爬取，没有写完代码就放弃了。决心使用下面第3种方法爬取
	3、采用图像识别和抓包工具配合爬取；使用了C++, Python, 和JScript；基本实现
	无人值守。
	"""
	name = "landchina"

	now = None
	today = None
	settings = None
	root_path = None
	log_dir = None
	main_log_file_path = None
	debug = False
	crawled_dir = None
	html_dir = None
	output_folder_name = None
	input_folder_name = None
	base_uri = None
	browser = None
	tabid_list = None
	input_keyword_dict = None
	list_csv_file_path = None
	wait_time = None
	missed_url_file_name = ""

	input_box_dict = {
		263: "TAB_QuerySubmitConditionData",
		226: "TAB_queryTblEnumItem_75",
	}

	keyword_english = {}
	replace_list = ["市本级", "市", "县", "区" ]

	def __init__(self ):
		self.init_self_attributes( )

	def init_self_attributes(self):
		self.now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		self.today = datetime.datetime.now().strftime("%Y%m%d")
		self.settings = settings
		self.root_path = self.settings.get( name="PROJECT_PATH", default="" )
		self.log_dir = self.settings.get( name="LOG_DIR", default="" )
		self.main_log_file_path = os.path.join( self.log_dir, self.settings.get( name="MAIN_LOG_FILE_NAME", default="" ) )
		self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False )
		self.crawled_dir = self.settings.get( name="CRAWLED_DIR", default = "" )
		self.html_dir = self.settings.get( name="HTML_DIR", default = "" )
		self.output_folder_name = self.settings.get( name = "OUTPUT_FOLDER_NAME", default="" )
		self.input_folder_name = self.settings.get( name = "INPUT_FOLDER_NAME", default="" )
		self.base_uri = self.settings.get( name = "BASE_URI", default="" )
		self.browser = self.settings.get( name = "BROWSER", default="" )
		self.tabid_list = self.settings.get( name = "TABID_LIST", default="" )
		self.input_keyword_dict = self.settings.get( name = "INPUT_KEYWORD_DICT", default="" )
		self.list_csv_file_path = os.path.join( self.crawled_dir, f"landchina_list_{self.today}.csv" )
		self.wait_time = 2 if self.debug else 3
		self.maximal_requests = self.settings.get( name = "MAXIMAL_REQUESTS", default=50 )
		self.missed_url_file_name = self.settings.get( name = "MISSED_URL_FILE_NAME", default="" )
		self.keyword_english = self.settings.get( name = "KEYWORD_ENGLISH", default={} )

	def make_uri_list(self):
		url_list = []
		for one_id in self.tabid_list:
			url_list.append( f"{self.base_uri}?tabid={one_id}" )
		return url_list

	def send_keywords(self):
		"""
		revision: 20190813
		"""
		url_list = self.make_uri_list()
		log_file_path = os.path.join( self.log_dir, self.missed_url_file_name )
		for index, one_url in enumerate(url_list):
			tabid = self.tabid_list[ index ]
			keyword_list = self.input_keyword_dict[tabid]
			input_box_xpath = self.input_box_dict[tabid]
			for keyword in keyword_list:
				keyword_en = self.keyword_english[keyword] if keyword in self.keyword_english.keys() else keyword

	def parse_one_index_page_response_field(self, webdriver = None ):
		info_list = []
		if webdriver is None:
			return info_list

		tr_list = webdriver.find_elements_by_xpath( "//table[@id='TAB_contentTable']/tbody/tr[not(@class='gridHeader')]" )
		for one_tr in tr_list:
			td_list = one_tr.find_elements_by_xpath("./td")
			value_list = []
			this_row_dict = {}
			link = ""
			for one_td in td_list:
				value_list.append( one_td.text )
				link_a = self.get_element( webdriver = one_td, xpath = "./a", elements_bool = False, use_id = False )
				if link_a is not None and 1 > len(link):
					link = link_a.get_attribute("href")
			if 4 == len( value_list ):
				this_row_dict["序号"] = value_list[0].replace(".", "")
				this_row_dict["行政区代码"] = value_list[1]
				this_row_dict["标题"] = value_list[2]
				this_row_dict["发布时间"] = value_list[3]
				this_row_dict["detailed_url"] = link
				info_list.append(this_row_dict)

		return info_list
	
	def execute(self):
		if type(self.tabid_list) not in [list] or type(self.input_keyword_dict) not in [dict] or 1 > len( self.tabid_list ):
			error_msg = f"self.tabid_list or self.input_keyword_dict is NOT correct: {self.tabid_list}, {self.input_keyword_dict}"
			content = f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}"
			CommonMethodClass.write_log( content = content, log_file_path = self.main_log_file_path )
			return False
		for one_category in self.tabid_list:
			if one_category not in self.input_keyword_dict.keys():
				error_msg = f"{one_category} is NOT in {self.input_keyword_dict.keys()}"
				content = f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}"
				CommonMethodClass.write_log( content = content, log_file_path = self.main_log_file_path )
				return False
		counter = self.do_requests(  )
		content = f"At {self.now}, {counter} requests have been sent"
		CommonMethodClass.write_log( content = content, log_file_path = self.main_log_file_path )

	def test(self):
		path = self.whereis_chromedriver()
		print( path )
		# print( self.district_name_dict )
		# district_list = ["南澳县", "佛山市本级", "连南瑶族自治县", "梅州市本级", "雷州市", ]
		# self.check_district_names( district_list = district_list, keyword = "广东省" )
	
if __name__=='__main__':
	app = LandchinaSpider( )
	# app.test()
	app.execute()
