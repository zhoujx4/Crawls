# coding: utf-8
import requests
import sys
import random
import time
import json
import hashlib
from requests.exceptions import RequestException

class ProxyAgent(object):

	@classmethod
	def control_the_windows_vpn(cls):
		"""
			documentation for controlling the: http://www.xunlianip.com/api-doc
			todo...
		"""
		pass

	@classmethod
	def get_server_ip(cls):
		url = "https://www.coursehelper.site/index/index/getHeaders"
		now = int(time.time())
		token = f"Guangzhou{str(now)}"
		m = hashlib.md5()  
		m.update( token.encode(encoding = 'utf-8') )
		params = {
			"token": m.hexdigest(),
		}

		response = requests.get(url, params=params)
		if 200 == response.status_code:
			resp_dict = json.loads( response.text )
			if "REMOTE_ADDR" in resp_dict.keys() and "HTTP_X_FORWARDED_FOR" in resp_dict.keys():
				forwarded = resp_dict["HTTP_X_FORWARDED_FOR"]
				remote_addr = resp_dict["REMOTE_ADDR"]
				forwarded_list = forwarded.split(",")
				temp_list = []
				for one in forwarded_list:
					if -1 == one.find( remote_addr ):
						temp_list.append( one )
				
				if 0 == len( temp_list ):
					return [remote_addr]
				else:
					return forwarded_list
			else:
				return []
		else:
			return []

	@classmethod
	def setup_xunlian_white_ip(cls, setup_xunlian_dict = {}, headers={}, logger = None):
		"""
			Todo: as of 20190610, only this response.text == {"code":10000,"success":false,"msg":"缺少必要参数"} returns!
		"""
		setup_ok = False
		if setup_xunlian_dict is None or not isinstance( setup_xunlian_dict, dict ):
			setup_xunlian_dict = {
				"proxy_user": "gz2010yu",
				"proxy_pwd": "entrobus28",
			}
		if "white_ip" not in setup_xunlian_dict.keys() or 1 > len( setup_xunlian_dict["white_ip"] ):
			temp_list = cls.get_server_ip()
			if 1 > len( temp_list ) or 1 > len( temp_list[0] ):
				return setup_ok
			setup_xunlian_dict["white_ip"] = temp_list[0]
		if "proxy_user" not in setup_xunlian_dict.keys() or 1 > len( setup_xunlian_dict["proxy_user"] ):
			setup_xunlian_dict["proxy_user"] = "gz2010yu"
		if "proxy_pwd" not in setup_xunlian_dict.keys() or 1 > len( setup_xunlian_dict["proxy_pwd"] ):
			setup_xunlian_dict["proxy_pwd"] = "entrobus28"
		
		params = {
			"appid": setup_xunlian_dict["proxy_user"],
			"appkey": setup_xunlian_dict["proxy_pwd"],
			"white_ip": setup_xunlian_dict["white_ip"],
		}
		base_uri_for_ip_whitelist = f"http://h.xunlianip.com/Users-whiteIpAddNew.html"
		resp = requests.get(base_uri_for_ip_whitelist, params=params, headers=headers )
		# print( resp.text ) # {"code":10000,"success":false,"msg":"缺少必要参数"}
		if hasattr( resp, "status_code" ) and hasattr( resp, "text" ) and 200 == resp.status_code:
			result_dict = json.loads( resp.text )
			if "code" in result_dict.keys() and 0 == int(result_dict["code"]):
				setup_ok = True
		if not setup_ok and logger is not None and hasattr( logger, "error" ):
			logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, fail to setup a white ip: {resp.text}" )
		
		return setup_ok

	@classmethod
	def initialize_params_for_proxy_ip(cls, params_for_proxy_ip = {}):
		default_dict = {
			"packid": 1,
			"qty": 1,
			"port": 1,
			"format": "json",
			"ss": 1,
			"css": "",
			"ipport": 1,
			"et": 0,
			"pi": 0,
			"co": 0,
			"pro": "",
			"city": "",
		}
		if params_for_proxy_ip is None or 1 > len( params_for_proxy_ip ):
			return default_dict
		for index, key in enumerate( params_for_proxy_ip ):
			default_dict[ key ] = params_for_proxy_ip[ key ]
		return default_dict

	@classmethod
	def request_proxy_ip(cls, params_for_proxy_ip = {}, headers={}, logger = None):
		resp = ""
		base_uri_for_proxy_ip = "http://47.106.170.4:8081/Index-generate_api_url.html"
		resp = requests.get(base_uri_for_proxy_ip, params=params_for_proxy_ip, headers=headers )
		# print( resp.text ) # {"code":10002,"success":"false","msg":"请选择已购买的套餐"}
		if "format" in params_for_proxy_ip.keys() and "json" == params_for_proxy_ip["format"]:
			try:
				resp_dict = json.loads(resp.text)
			except Exception as ex:
				if logger is not None and hasattr( logger, "error" ):
					logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, proxy server return unknown text ({resp})" )
				return 599, {"response": resp}
			else:
				if "code" not in resp_dict.keys():
					if logger is not None and hasattr( logger, "error" ):
						logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, proxy server return unknown text ({resp})" )
					return 598, resp_dict
				if 0 != resp_dict["code"]:
					if logger is not None and hasattr( logger, "error" ):
						logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, proxy server return error code ({resp_dict['code']})" )
					return int( resp_dict["code"] ), resp_dict
				if "data" not in resp_dict.keys():
					if logger is not None and hasattr( logger, "error" ):
						logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, proxy server did not return resp_dict['data'] " )
					return 597, resp_dict
				if logger is not None and hasattr( logger, "info" ):
					logger.info( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, proxy server returns {resp_dict['data']} " )
				return 0, resp_dict
		if logger is not None and hasattr( logger, "error" ):
			logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, params_for_proxy_ip['format'] != 'json' " )
		return 499, {}

	@classmethod
	def extract_good_ip(cls, ip_list = [], delay = 1.0):
		return_list = []
		now = time.time()
		ip_port = False
		if 0 < len(ip_list) and "IP" in ip_list[0].keys() and -1 < ip_list[0]["IP"].find(":"):
			ip_port = True
		for one_ip in ip_list:
			if "ExpireTime" in one_ip.keys():
				time_array = time.strptime( one_ip["ExpireTime"], "%Y-%m-%d %H:%M:%S" )
				time_stamp = float(time.mktime(time_array))
				if time_stamp > now + delay:
					return_list.append( one_ip["IP"] if ip_port else f"{one_ip['IP']}:{one_ip['Port']}" )
			else:
				# the proxy server did not has ExpireTime
				# [{'IP': '115.226.225.234:48095'}]
				return_list.append( one_ip["IP"] if ip_port else f"{one_ip['IP']}:{one_ip['Port']}" )
		return return_list

	@classmethod
	def get_next_good_ip(cls, available_ip_list=[]):
		if 1 > len( available_ip_list ):
			return ""
		elif 1 == len( available_ip_list ):
			return available_ip_list[0]
		pointer = random.randint(0, len(available_ip_list) )
		return available_ip_list[pointer]

	@classmethod
	def get_xunlian_proxy_dict(cls, headers = {}, params_for_proxy_ip={}, setup_xunlian_dict = None, need_setup_xunlian = False, logger= None):
		"""
			the proxy webpage is: http://h.xunlianip.com/Shop-index.html
		"""
		proxies_dict = {}
		if not isinstance(headers, dict) or 1 > len(headers):
			headers = {
				"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
			}
		setup_ok = True
		if need_setup_xunlian:
			setup_ok = cls.setup_xunlian_white_ip( setup_xunlian_dict = setup_xunlian_dict, logger = logger)

		if setup_ok:
			available_ip_list = []
			params_for_proxy_ip = cls.initialize_params_for_proxy_ip( params_for_proxy_ip = params_for_proxy_ip   )
			status_code, resp_dict = cls.request_proxy_ip( params_for_proxy_ip = params_for_proxy_ip, headers = headers, logger = logger )
			if 0 == status_code:
				available_ip_list = cls.extract_good_ip( ip_list = resp_dict["data"], delay = 1.0 )
				if 0 < len( available_ip_list ):
					next_good_ip = cls.get_next_good_ip( available_ip_list = available_ip_list )
					proxies_dict = {
						"http": f"http://{next_good_ip}",
						"https": f"http://{next_good_ip}",
					}

		if 1 > len( proxies_dict ) and logger is not None and hasattr( logger, "error" ):
			logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, no proxy ip returned" )
		return proxies_dict


	# returns 0, 10000, 10001, 10002, 10003, -1, -2, -3
	@classmethod
	def xunlian_proxy(cls, target_url = '', params={}, headers = {}, cookies={}, method="get", params_for_proxy_ip={}, setup_xunlian_dict = None, need_setup_xunlian = False, logger= None ):
		if 1 > len(target_url):
			return (-1, f"wrong parameters. target_url = {target_url}")
		if not isinstance(headers, dict) or 1 > len(headers):
			headers = {
				"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
			}

		setup_ok = True
		if need_setup_xunlian:
			setup_ok = cls.setup_xunlian_white_ip( setup_xunlian_dict = setup_xunlian_dict, logger = logger)
		
		if 1 > len(target_url):
			return (-1, f"wrong parameters. target_url = {target_url}", params)

		if setup_ok:
			available_ip_list = []
			params_for_proxy_ip = cls.initialize_params_for_proxy_ip( params_for_proxy_ip = params_for_proxy_ip   )
			status_code, resp_dict = cls.request_proxy_ip( params_for_proxy_ip = params_for_proxy_ip, headers = headers, logger = logger )
			if 0 == status_code:
				available_ip_list = cls.extract_good_ip( ip_list = resp_dict["data"], delay = 1.0 )
				next_good_ip = cls.get_next_good_ip( get_next_good_ip = get_next_good_ip )
				proxies = {
					"http": f"http://{next_good_ip}",
					"https": f"http://{next_good_ip}",
				}

				while True:
					try:
						if "get" == method:
							resp = requests.get(target_url, params=params, headers=headers, cookies=cookies, proxies=proxies) # .content.decode()
						elif "post" == method:
							resp = requests.post(target_url, params=params, headers=headers, cookies=cookies, proxies=proxies)
						else:
							if logger is not None and hasattr( logger, "error" ):
								logger.error( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, method shall ONLY be get or post" )
							return (-1, "method shall be get or post, and a str", params)
					except RequestException as ex:
						return cls.xunlian_proxy( target_url=target_url, params=params, headers=headers, cookies=cookies, method=method, params_for_proxy_ip=params_for_proxy_ip, setup_xunlian_dict=setup_xunlian_dict, need_setup_xunlian=False, logger=logger )
					except Exception as ex:
						return ( -2, f"Exception happens while crawling {target_url} Exception = {ex}", params )
					else:
						# todo
						print( resp.text )
						# if hasattr(resp, 'status_code') and 200 == resp.status_code:
						# 	temp_dict = eval( resp.text )
						# 	if 0 == int(temp_dict["code"]):
						# 		if return_params:
						# 			return (200, f"{str(params)}======{resp.text}\n")
						# 		else:
						# 			return (200, resp.text)
						# 	elif -100 == int(temp_dict["code"]):
						# 		return ( -100, str(params) )
						# elif hasattr(resp, 'status_code'):
						# 	return (0, f"Wrong status code returned. resp.status_code = {resp.status_code}")
						# else:
						# 	return (0, f"Unknown error from server. no resp.status_code! ")
						return (0, resp.text, params )
		return ( -3, f"need next proxy.", params )
