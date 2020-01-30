# coding=utf-8
try:
	from pyocr import pyocr
	import fitz
	import datetime
	import time
	from time import sleep
	import re
	import os
	import sys
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

	from land.settings import settings

except ImportError as ex:
	print( f"ImportError: {ex}" )
	raise SystemExit

class LandSpider(object):
	"""
	本类是为碧桂园土地投策部门收集数据，提供给熵商公司算法组同事进行建模和后端组上图的多个爬虫和图像识别
	爬取目标网站是政府网站，网址类似如下：
	广州：http://www.gzggzy.cn/cms/html/wz/view/index/layout2/tdkc_fwzq_wtr.html?channelId=752
	佛山：http://www.fsggzy.cn/
	revision: 20190804, 20190802
	主要涉及的方法有：
		1、数据源爬取
		2、pdf文件读取和转存png图片
		3、ocr中文和数字识别
		4、西安坐标系/佛山2000坐标系等地方坐标系转百度经纬度
	"""
	name = "land"

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
	webdriver = None

	baidumap_level_dict = {
		"1000 公里": 4,
		"500 公里": 5,
		"200 公里": 6,
		"100 公里": 7,
		"50 公里": 8,
		"25 公里": 9,
		"20 公里": 10,
		"10 公里": 11,
		"5 公里": 12,
		"2 公里": 13,
		"1 公里": 14,
		"500 米": 15,
		"200 米": 16,
		"100 米": 17,
		"50 米": 18,
		"20 米": 19,
	}

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
		self.output_folder_name = self.settings.get( name = "OUTPUT_FOLDER_NAME", default="" )
		self.input_folder_name = self.settings.get( name = "INPUT_FOLDER_NAME", default="" )
		self.base_uri = self.settings.get( name = "BASE_URI", default="" )
		self.browser = self.settings.get( name = "BROWSER", default="" )

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

	def read_pdf_and_save_png(self, filename, path, pic_dir):
		"""
		revision: 20190804
		references:
			https://my.oschina.net/u/2396236/blog/1798170
			https://github.com/pymupdf/PyMuPDF/blob/master/demo/demo.py
		"""
		doc = fitz.open(path)
		new_file_name = filename.replace(".pdf", "")

		for page_index in range(doc.pageCount):
			print( page_index )
			page = doc[page_index]
			zoom = int(100)
			rotate = int(0)
			trans = fitz.Matrix(zoom / 100.0, zoom / 100.0).preRotate(rotate)

			# create raster image of page (transparent)
			pm = page.getPixmap(matrix=trans, alpha=True)

			# write a PNG image of the page
			pm.writePNG( f"{new_file_name}___{page_index}.png" )

	def get_current_level(self, chrome_driver = None ):
		"""
			revision: 20190804
		"""
		error_msg = ""
		try:
			level = int( chrome_driver.find_element_by_id( "ZoomNum" ).text )
			if isinstance( level, int ) and -1 < level: return level
		except WebDriverException as ex1:
			try:
				level_text = chrome_driver.find_element_by_xpath( '//div[@class=" BMap_scaleCtrl BMap_noprint anchorBL"]/div[@class="BMap_scaleTxt"]' ).text
				if level_text in self.baidumap_level_dict.keys():
					return self.baidumap_level_dict[level_text]
				else:
					error_msg = f"{level_text} is NOT a key of self.baidumap_level_dict ({self.baidumap_level_dict})"
			except WebDriverException as ex:
				error_msg = f"fail to find div containing Class BMap_scaleCtrl BMap_noprint anchorBL. WebDriverException = {ex}"
			except Exception as ex:
				error_msg = f"fail to find div containing Class BMap_scaleCtrl BMap_noprint anchorBL. Exception = {ex}"
		except Exception as ex:
			error_msg = f"fail to find div containing id ZoomNum. Exception = {ex}"
		
		if 0 < len(error_msg):
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return -1

	def webdriver_zoom(self, chrome_driver = None, level_int = 16 ):
		"""
			revision: 20190804
		"""
		try:
			level = self.get_current_level(chrome_driver = chrome_driver)
			if -1 == level: return -1
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

	def visit_gz_map(self, url):
		"""
		revision: 20190804
		1、首先使用webdriver访问http://tkwz.gzggzy.cn/gtkcwz/module/wz/ydjh.jsp以后得到图标为20公里的百度地图
		2、调整地图级别到16级（200米）
		3、返回chrome_driver
		"""
		cookies, url_back, title = "", "", ""
		error_msg = ""
		header_dict = self.get_headers(self.browser)
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
			self.webdriver = chrome_driver
			print( self.webdriver )
			return cookies, url_back, title
		except WebDriverException as ex:
			error_msg = f"WebDriverException happended while operating webdriver. WebDriverException = {ex}"
		except Exception as ex:
			error_msg = f"WebDriverException happended while operating webdriver. Exception = {ex}"
		self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		return cookies, url_back, title

	def click_for_new_window(self ):
		print("into click_for_new_window")
		try:
			tr_list = self.webdriver.find_elements_by_xpath( '//tbody[@id="cjtablebody"]/tr' )
			print( tr_list )
			for one_tr in tr_list:
				print( one_tr )
				this_a = one_tr.find_element_by_xpath( './tr/td/a' )
				lng_lat_str = this_a.get_attribute("onclick")
				this_land = this_a.text
				print( f"lng_lat_str = {lng_lat_str}; this_land = {this_land}" )
				this_a.click()
				self.webdriver.implicitly_wait(30)

				# 点击最中央的那个地块
				old_handles = driver.window_handles
				print( f"old_handles == {old_handles}" )
				span_list = self.webdriver.find_elements_by_xpath( '//div[@id="container"]/div/div[@class="BMap_mask"]/following-sibling::div/div/following-sibling::div/span[@class="BMap_Marker BMap_noprint"]' )
				center_land = span_list[0]
				center_land.click()
				self.webdriver.implicitly_wait(30)
				all_handles = self.webdriver.window_handles
				print(all_handles)
				self.webdriver.implicitly_wait(30)

				#拿到新窗口句柄 并切换到新窗口
				newhandle = [handle for handle in all_handles if handle not in old_handles]
				self.webdriver.switch_to.window(newhandle[0])
				print(self.webdriver.title)
				break
		except Exception as ex:
			error_msg = f"WebDriverException happended while operating webdriver. Exception = {ex}"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )

	def pyocr_one_image(self, image_path ):
		"""
		revision: 20190804
		Author: https://blog.csdn.net/HuangZhang_123/article/details/61920975
		references:
			tesseract OCR官网针对大部分linux系统可以直接命令行安装：https://github.com/tesseract-ocr/tesseract/wiki
			tesseract OCR5.0.0 windowns 64位下载地址：https://github.com/UB-Mannheim/tesseract/wiki
			如果海外网速慢，国内4.0版本下载地址是：http://www.xue51.com/soft/1594.html
			简体中文训练集：https://github.com/tesseract-ocr/tessdata/blob/master/chi_sim.traineddata
			繁体中文训练集：https://github.com/tesseract-ocr/tessdata/blob/master/chi_tra.traineddata
			官网文档：https://digi.bib.uni-mannheim.de/tesseract/doc/

			pyocr官网：https://gitlab.gnome.org/World/OpenPaperwork/pyocr

			博文：
			（只在命令行训练/运行tesseract-OCR）Tesseract-OCR识别中文与训练字库实例：https://www.cnblogs.com/wzben/p/5930538.html
			https://blog.csdn.net/qq_37193537/article/details/81335165
		"""
		os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
		
		tools = pyocr.get_available_tools()[:]
		if 1 > len(tools):
			error_msg = f"No OCR tool found"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
			return False
		#查找OCR引擎
		self.write_log( f"Using {tools[0].get_name()} to ocr {image_path}" )
		#lang='chi_sim'为OCR的识别语言库。C:\Program Files\Tesseract-OCR\tessdata
		return tools[0].image_to_string(Image.open( image_path ),lang="chi_sim")

	def test1(self):
		"""
		命令行：tesseract 7.png 7.txt -l chi_sim
		"""
		attachment_dir = os.path.join( self.crawled_dir, "attachments" )
		attachment_list = os.listdir( attachment_dir )
		for attachment in attachment_list:
			if attachment.endswith( ".pdf" ):
				pdf_file_path = os.path.join( attachment_dir, attachment )
				self.read_pdf_and_save_png( attachment, pdf_file_path, attachment_dir )

	def test2(self):
		cookies, url_back, title = self.visit_gz_map( url = "http://tkwz.gzggzy.cn/gtkcwz/module/wz/ydjh.jsp" )
		print( f"cookies, url_back, title = {cookies, url_back, title}" )
		self.click_for_new_window( )
		# level = self.webdriver_zoom( chrome_driver = chrome_driver, level_int = 16 )
		sleep(30)

	def test3( self ):
		for one_file in os.listdir( self.crawled_dir ):
			one_file = "2019-08-01_2cd43b08-fe89-4ce9-8061-b3e97b8515e3_5.jpg"
			image_path = os.path.join( self.crawled_dir, one_file )
			ocr_result = self.pyocr_one_image( image_path = image_path )
			print( ocr_result )
			break

if __name__=='__main__':
	app = LandSpider( )
	app.test3()
