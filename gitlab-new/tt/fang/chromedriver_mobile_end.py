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
from urllib import parse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

class CookieException(Exception):
	def __init__(self):
		Exception.__init__(self)

class easygospider(object):
	"""
	20190729发现fang.com有新反爬措施
	https://mp.weixin.qq.com/s/LahzheUnV0YNpZnY1bbFFA
	"""
	user_agent = None
	referer = None
	browser = None

	def __init__(self ):
		self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36" # pc user agent

		# self.user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1" # mobile end
		self.referer = "https://sh.zu.fang.com/"
		self.browser = "Chrome"

	def save_html(self, content = "", url = "" ):
		if not isinstance( url, str ) or 1 > len( url ) or type(content) not in [str, bytes] or 1 > len( content ):
			return False
		html_filename, html_file_path, detailed_page, city_name, apt_id = self.get_file_path( url = url )
		try:
			if isinstance( content, str ):
				with open( html_file_path, "a", encoding="utf-8" ) as f: # newline="", errors="ignore"
					f.write( content )
			elif isinstance( content, bytes ):
				with open( html_file_path, "wb" ) as f:
					f.write(content)
			else:
				with open( html_file_path, "wb" ) as f:
					f.write( bytes(content) )
		except Exception as ex:
			print( f"Exception happened while writing to {html_file_path}. Exception = {ex}" )

	def get_file_path(self, url = ""):
		"""
		detailed page:			https://gz.zu.fang.com/chuzu/3_238110671_1.htm?channel=3,8
		list page (first):		https://gz.zu.fang.com/
		list page (next):		https://gz.zu.fang.com/house/i32/
		"""
		apt_id = ""
		city_name = ""
		detailed_page = False
		html_filename = ""
		html_file_path = ""

		if not isinstance( url, str ) or 1 > len( url ):
			return html_filename, html_file_path, detailed_page, city_name, apt_id

		result_obj = parse.urlparse( url )
		now = datetime.datetime.now()
		html_filename = "{}.html".format( now.strftime("%Y%m%d_%H%M%S") )
		today = f'{now.strftime("%Y%m%d")}'
		url_path = ""

		if hasattr( result_obj, "netloc" ) and result_obj.netloc is not None and 0 < len( result_obj.netloc ):
			temp_list = result_obj.netloc.split(".")
			city_name = temp_list[0]

		if hasattr( result_obj, "path") and result_obj.path is not None and 0 < len( result_obj.path ):
			url_path = result_obj.path
			print( f"type of url_path is {type(url_path)}" )
			if -1 < url_path.find( ".htm" ):
				detailed_page = True
				temp_list = url_path.split("_")
				if 1 < len(temp_list): apt_id = f"{temp_list[1]}"
		
		if detailed_page:
			html_filename = f"{city_name}_{apt_id}_{today}.html"
		elif 1 > len( url_path ):
			html_filename = f"{city_name}_index1_{today}.html"
		elif 0 < len( url_path ):
			temp_list = url_path.split("/")
			if 0 < len( temp_list ):
				last_part = temp_list[ len( temp_list ) - 1 ]
				page = last_part[2:]
				html_filename = f"{city_name}_index{page}_{today}.html"
		
		if 0 < len( html_filename ):
			html_file_path = os.path.join( self.detail_html_dir, html_filename )
		return html_filename, html_file_path, detailed_page, city_name, apt_id

	def open_webdriver(self, chrome_url_list = []):
		if not isinstance( chrome_url_list, list ):
			return False
		chrome_obj = None
		try:
			chrome_options = Options()
			chrome_options.add_argument('accept="application/json"')
			chrome_options.add_argument( f"referer={self.referer}" )
			chrome_options.add_argument( f"user-agent={self.user_agent}" )
			chrome_options.add_argument( "lang=zh_CN.UTF-8" )
			# chrome_options.add_argument('--headless') # 在广州分公司将无头配置项注销掉，直接在windows下运行
			chrome_obj = webdriver.Chrome(options=chrome_options, executable_path="chromedriver.exe") # 使用self.find_exe_in_path来查找这个文件所在的文件夹
			chrome_obj.implicitly_wait(30)

			for chrome_url in chrome_url_list:
				chrome_obj.get( chrome_url ) # "https://sh.zu.fang.com/"
				cookies = chrome_obj.get_cookies()
				if isinstance( cookies, dict ) and 0 < len( cookies ):
					chrome_obj.add_cookie( cookies )
				print( f"chrome_obj.title = {chrome_obj.title}; cookies = {cookies}; type of cookies = {type(cookies)}" )
				self.write_log( dir(chrome_obj) )
				self.save_html( chrome_obj.content, chrome_url )
				time.sleep(5)
		except WebDriverException as ex:
			self.write_log( f"WebDriverException happended while getting cookies. WebDriverException = {ex}" )
		finally:
			try:
				if chrome_obj is not None:
					chrome_obj.close()
			except Exception as ex:
				self.write_log( f"Exception happended while closing chrome_obj in Method get_cookie.; Exception = {ex}" )
		chrome_obj.quit()

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

	def read_env_variable(self, variable = "PATH"):
		path = os.environ.get( variable )
		if not isinstance( path, str ):
			self.write_log( f"{path} is not a string" )
			return False

		path_list = []
		for one in path.split(";"):
			if 0 < len( one ):
				path_list.append( os.path.join(one) )
		return path_list

	def find_exe_in_path( self, exe_file = "chromedriver.exe" ):
		path_list = self.read_env_variable()
		dir_list = []
		for one in path_list:
			if not os.path.isdir(one):
				continue
			file_name_list = os.listdir(one)
			if exe_file in file_name_list:
				dir_list.append( one )
		self.write_log( f"{exe_file} is found in {dir_list}")
		return dir_list

if __name__ == "__main__":
	app = easygospider( )
	app.open_webdriver( )
	# dir_list = app.find_exe_in_path()
	# chromedriver.exe is found in ['C:\\Program Files (x86)\\Google\\Chrome\\Application']
