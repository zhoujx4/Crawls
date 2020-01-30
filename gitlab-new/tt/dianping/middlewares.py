import logging
import json
import re

import scrapy
from scrapy import signals
from scrapy.http import Request
from twisted.internet import defer
from scrapy.spiders import CrawlSpider
from scrapy.exceptions import NotConfigured

from tt.extensions.commonfunctions import CommonClass

class ProxyDownloaderMiddleware(object):
	"""ProxyDownloaderMiddleware"""
	proxy_meta = {}

	def __init__(self, proxy_meta = {}):
		super(ProxyDownloaderMiddleware, self).__init__()
		self.proxy_meta = proxy_meta

	def process_request(self,request,spider):
		if self.proxy_meta is None or not isinstance( self.proxy_meta, dict ) or 1 > len( self.proxy_meta ):
			self.proxy_meta = CommonClass.get_proxies( proxy_dict = {} )
		if request.url.startswith("http://"):
			request.meta['proxy'] = self.proxy_meta['http']
		elif request.url.startswith("https://"):
			request.meta['proxy'] = self.proxy_meta['https']
		
class DianpingDownloaderMiddleware(object):
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
