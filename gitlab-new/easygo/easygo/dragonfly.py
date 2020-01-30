# coding: utf-8
import requests
from requests.exceptions import RequestException

class Dragonfly(object):

	# returns 0, 200, -100, -1, -2, -3
	@classmethod
	def dragonfly(cls, target_url = '', params={}, headers = {}, cookies={}, method="get", return_params=False, proxy_pwd = "00rPeu7HKvmu", proxy_user = "JEVJ1625573267906612", proxy_host = "dyn.horocn.com", proxy_port = "50000"):
		resp = ''
		if 1 > len(target_url): # or 1 > len( proxy_user ) or 1 > len( proxy_pwd ):
			return (-1, f"wrong parameters. target_url = {target_url}")

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
			"http": proxy_meta,
			"https": proxy_meta,
		}

		while True:
			try:
				if "get" == method:
					resp = requests.get(target_url, params=params, headers=headers, cookies=cookies, proxies=proxies) # .content.decode()
				elif "post" == method:
					resp = requests.post(target_url, params=params, headers=headers, cookies=cookies, proxies=proxies)
				else:
					resp = "method shall be get or post, and a str"
					return (-1, resp)
			except RequestException as ex:
				return cls.dragonfly( target_url=target_url, params=params, headers=headers, cookies=cookies, method=method, return_params=return_params, proxy_user=proxy_user, proxy_pwd=proxy_pwd, proxy_host=proxy_host, proxy_port=proxy_port )
			except Exception as ex:
				return ( -2, f"Exception happens while crawling {target_url} Exception = {ex}" )
			else:
				if hasattr(resp, 'status_code') and 200 == resp.status_code:
					temp_dict = eval( resp.text )
					if 0 == int(temp_dict["code"]):
						if return_params:
							return (200, f"{str(params)}======{resp.text}\n")
						else:
							return (200, resp.text)
					elif -100 == int(temp_dict["code"]):
						return ( -100, str(params) )
				elif hasattr(resp, 'status_code'):
					return (0, f"Wrong status code returned. resp.status_code = {resp.status_code}")
				else:
					return (0, f"Unknown error from server. no resp.status_code! ")
		return ( -3, f"need next proxy." )
