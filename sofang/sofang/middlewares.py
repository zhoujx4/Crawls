# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import scrapy
from scrapy import signals
import base64
import threading
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware


class SofangSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class SofangDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)



# 代理服务器

# proxyServer = "[http://dyn.horocn.com:50000](http://dyn.horocn.com:50000/)"
# proxyServer = "http://dyn.horocn.com:50000"
#
# # 代理隧道验证信息
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




        #
        # proxy = 'http://dyn.horocn.com:50000'
        # user_password = "YXXK1640539698240346:cILp7fqzoqzM"
        # request.meta['proxy'] = proxy
        # # bytes
        # b64_user_password = base64.b64encode(user_password.encode('utf-8'))
        #
        # request.headers['Proxy-Authorization'] = 'Basic '\
        #                                          + b64_user_password.decode('utf-8')


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

        if response.status != 200:
            request.meta["proxy"] = proxyServer
            request.headers["Authorization"] = proxyAuth
            return request
        return response
