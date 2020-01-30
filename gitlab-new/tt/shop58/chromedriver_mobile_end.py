#! /usr/local/bin/python3
# coding: utf-8
# __author__ = "lsg"
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

class CookieException(Exception):
	def __init__(self):
		Exception.__init__(self)

class easygospider(object):
	"""
	https://m.58.com/gz/shangpucz/?reform=pcfront
	20190725发现58.com针对pc端已经全面反爬。反爬结果会将请求转跳到这个陷阱：https://404.58.com/404.html?from=https://info5.58.com/gz/shangpu/
	主要反爬措施包括，(1)检测webdriver；(2)检测浏览器User Agent
	经过周俊贤测试发现，只需要更换User Agent为火狐即可
	"""
	user_agent = None
	referer = None
	browser = None

	def __init__(self ):
		# self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36" # pc user agent
		# pc end will be redirected to a pitfall at https://404.58.com/404.html?from=https://info5.58.com/gz/shangpu/

		self.user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1" # mobile end
		self.referer = "https://gz.58.com"
		self.browser = "Chrome"

	def open_webdriver(self):
		chrome_login = None
		try:
			chrome_options = Options()
			chrome_options.add_argument('accept="application/json"')
			chrome_options.add_argument( f"referer={self.referer}" )
			chrome_options.add_argument( f"user-agent={self.user_agent}" )
			chrome_options.add_argument( "lang=zh_CN.UTF-8" )
			# chrome_options.add_argument('--headless') # 在广州分公司将无头配置项注销掉，直接在windows下运行
			chrome_login = webdriver.Chrome(options=chrome_options, executable_path="chromedriver.exe") # 需要使用相同目录下的这个版本的chromedriver.exe
			chrome_login.implicitly_wait(30)
			chrome_login.get( "https://gz.58.com/shangpu/" )
			cookies = chrome_login.get_cookies()
			self.write_log( f"chrome_login.title = {chrome_login.title}; cookies = {cookies}" )
			self.write_log( dir(chrome_login) )
			time.sleep(35)
		except WebDriverException as ex:
			self.write_log( f"WebDriverException happended while getting cookies. WebDriverException = {ex}" )
		finally:
			try:
				if chrome_login is not None:
					chrome_login.close()
			except Exception as ex:
				self.write_log( f"Exception happended while closing chrome_login in Method get_cookie.; Exception = {ex}" )
		chrome_login.quit()

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
