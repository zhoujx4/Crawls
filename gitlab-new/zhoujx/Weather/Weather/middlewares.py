# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import base64
import random
from urllib import request
import re
from twisted.internet.defer import DeferredLock
from urllib import request

# 设置随机请求头
# class UserAgentDownloadMiddleware(object):
#     USER_AGENT = [
#
#     ]
#     def process_request(self, request, spider):
#         user_agent = random.choice(self.USER_AGENT)
#         request.headers['User-Agent'] = user_agent



# class IPProxyDownloadMiddleware(object):
#
#     def process_request(self, request, spider):
#         proxy = 'http://dyn.horocn.com:50000'
#         user_password = "YXXK1640539698240346:cILp7fqzoqzM"
#         request.meta['proxy'] = proxy
#         # bytes
#         b64_user_password = base64.b64encode(user_password.encode('utf-8'))
#
#         request.headers['Proxy-Authorization'] = 'Basic ' \
#                                                  + b64_user_password.decode('utf-8')
#
#         print('Basic ' \
#                                                  + b64_user_password.decode('utf-8'))
#         # print('换代理了')


#
# proxyServer = "http://dyn.horocn.com:50000"
#
# # 代理隧道验证信息
#
# proxyUser="YXXK1640539698240346"       #用户名
# proxyPass = "cILp7fqzoqzM"        #密匙
# proxyAuth = "Basic " + base64.urlsafe_b64encode(bytes((proxyUser + ":" + proxyPass), "ascii")).decode("utf8")
#
#
#
# class IPProxyDownloadMiddleware(object):
#
#     def process_request(self, request, spider):
#
#         request.meta["proxy"] = proxyServer
#
#         request.headers["Proxy-Authorization"] = proxyAuth

proxyServer = "http://transfer.mogumiao.com:9001"

# appkey为你订单的key
proxyAuth = "Basic " + 'Z0pWVTRzSWFhMmlXUEJ3VDpFMWlKZ3BIZDhoMzdhOFIx'

class ProxyMiddleware(object):
    def process_request(self, request, spider):
        request.meta["proxy"] = proxyServer
        request.headers["Authorization"] = proxyAuth

    def process_response(self, request, response, spider):
        '''对返回的response处理'''
        # 如果返回的response状态不是200，重新生成当前request对象

        if response.status != 200 and response.status != 301 and response.status != 302:
            request.meta["proxy"] = proxyServer
            request.headers["Authorization"] = proxyAuth
            return request
        return response
