# coding: utf-8
import requests
import time
from requests.exceptions import RequestException
from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.opera.options import Options
from selenium.common.exceptions import WebDriverException

class Dragonfly(object):

	# returns 0, 200, -100, -1, -2, -3
	@classmethod
	def dragonfly(cls, target_url = '', params={}, headers = {}, cookies={}, method="get", return_params=False, for_cookies=False, proxy_pwd = "", proxy_user = "", proxy_host = "dyn.horocn.com", proxy_port = "50000"):
		resp = ''
		if 1 > len(target_url) or 1 > len( proxy_user ) or 1 > len( proxy_pwd ):
			return (-1, f"wrong parameters")

		if not isinstance(headers, dict) or 1 > len(headers):
			headers = {
				"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
				"Referer": "http://c.easygo.qq.com/eg_toc/map.html?origin=csfw",
			}

		proxy_meta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
			"host": proxy_host,
			"port": proxy_port,
			"user": proxy_user,
			"pass": proxy_pwd,
		}

		proxies = {
			"httpProxy": proxy_meta,
			"noProxy": None,
			"proxyType": "MANUAL",
			"class": "org.openqa.selenium.Proxy",
			"autodetect": False,
		}

		try:
			options = Options()
			options.add_argument('accept="application/json"')
			options.add_argument('referer="http://c.easygo.qq.com/eg_toc/map.html?origin="')
			options.add_argument('user-agent="Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"')
			options.add_argument('lang=zh_CN.UTF-8')
			desired_capabilities = options.to_capabilities()
			desired_capabilities['proxy'] = proxies
			# options.add_argument('--headless') # 在广州分公司将无头配置项注销掉，直接在windows下运行

			# https://blog.csdn.net/vinson0526/article/details/51850929
			# driver = webdriver.Chrome(desired_capabilities = desired_capabilities, options=options, executable_path="chromedriver.exe")
			# 需要使用相同目录下的这个版本的chromedriver.exe；否则报版本错误

			# https://get.geo.opera.com/pub/opera/desktop/58.0.3135.47/win/
			# https://github.com/operasoftware/operachromiumdriver/releases # this one is only for Windows NT, cannot for Win10 Home Edition
			# executable_path="C:\\Entrobus\\projects\\crawl\\drivers\\operadriver.exe"
			driver = webdriver.Opera(desired_capabilities = desired_capabilities, options=options, executable_path="chromedriver.exe" )
			driver.implicitly_wait(30)
			driver.get( "http://c.easygo.qq.com/eg_toc/map.html?origin=csfw&cityid=110000" )
			# qq_num = "3382624374"
			# qq_passwd = "co07s9a4w6e"
			qq_num = "1934267750"
			qq_passwd = "yu101472"
			driver.find_element_by_id("u").send_keys(qq_num)
			driver.find_element_by_id("p").send_keys(qq_passwd)
			driver.find_element_by_id("go").click()
			#检查是否存在验证码
			if "手机统一登录" in driver.title: # 成功登陆以后变成：宜出行
				# raise CookieException
				print( f"the qq number need to safe verify is {qq_num}" )
				time.sleep(35)
			cookies = driver.get_cookies()
			driver.quit()
			driver.close()

			# save cookie
			cookies_dict = {}
			for cookie in cookies:
				cookies_dict[cookie["name"]] = cookie["value"]
			cookies_string = ""
			for index, one in enumerate(cookies_dict):
				cookies_string += f"{str( one)}:{cookies_dict[one]};"
			cookies_string = cookies_string.strip(";")
			return (200, cookies_string)
		except Exception as ex:
			driver.close()
			return (-2, f"Exception happens while crawling {target_url} Exception = {ex}")
