# -*- coding: utf-8 -*-

# Scrapy settings for tt project
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

import datetime
import os
import sys
import scrapy
# from scrapy.extensions.httpcache import DummyPolicy
# from scrapy.extensions.httpcache import FilesystemCacheStorage

PROJECT_PATH = os.getcwd()
SPIDER_NAME = "shop58"

DEFAULT_REQUEST_HEADERS = {
	"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
	"Accept-Language": "zh-CN,zh;q=0.9",
	"Referer": "https://gz.58.com",
}

# HTTPPROXY_ENABLED = True
HTTPPROXY_ENABLED = False

# this cache can be ON because we can pick where we stopped
HTTPCACHE_ENABLED = True
# HTTPCACHE_POLICY = DummyPolicy
# HTTPCACHE_STORAGE = FilesystemCacheStorage
HTTPCACHE_DIR = os.path.join( PROJECT_PATH, "cached/" )

if HTTPPROXY_ENABLED and HTTPCACHE_ENABLED:
	DOWNLOADER_MIDDLEWARES = {
		"scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware": 100,
		"scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 105,
	}
elif HTTPPROXY_ENABLED:
	DOWNLOADER_MIDDLEWARES = {
		"scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 105,
	}
elif HTTPCACHE_ENABLED:
	DOWNLOADER_MIDDLEWARES = {
		"scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware": 100,
	}
else:
	DOWNLOADER_MIDDLEWARES = {}

today = datetime.datetime.now().strftime("%Y%m%d")
LOG_DIR = os.path.join( PROJECT_PATH, SPIDER_NAME, "logs" )
LOG_FILE = os.path.join( LOG_DIR, f"log_{SPIDER_NAME}{today}.log" )
LOG_LEVEL = "INFO"
LOG_ENCODING = "utf-8"
LOG_STDOUT = True

# if debugging, can overwrite the project settings
PROJECT_DEBUG = False
# PROJECT_DEBUG = True

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"

# Obey robots.txt rules
# ROBOTSTXT_OBEY = True
ROBOTSTXT_OBEY = False

AJAXCRAWL_ENABLED = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 1

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False
COOKIES_ENABLED = True

ITEM_PIPELINES = {
	f'{SPIDER_NAME}.pipelines.Shop58Pipeline': 300,
}

# 20190423接到通知，将8个城市缩减成为下面3个城市
CITY_LIST = [
	# "sz",
	"gz",
	# "fs",
	# "dg",
	# "zh", # 珠海
	# "zs", # 中山
	# "huizhou",
	# "jm", # 江门
	# "sg", # 韶关
	# "shaoyang", # 邵阳
	# "yy", # 岳阳
	# "zhuzhou", # 株洲
]
CITY_NAMES = [
	# "shenzhen",
	"guangzhou",
	# "foshan",
	# "dongguan"
	# "zhuhai",
	# "zhongshan",
	# "huizhou",
	# "jiangmen",
	# "shaoguan",
	# "shaoyang",
	# "yueyang",
	# "zhuzhou",
]
CRAWL_BATCHES = 1

# AMAP keys
AMAP_KEYS = [
	'4ebb849f151dddb3e9aab7abe6e344e2', # Peter的，每天300000次
	'470fdf698e3aab758d4cb026244f5194', # 下面5个都是曾基的同一个认证开发者账号，每天300000次
	'740f50c6fabd5801d0fad1cba62446d9',
	'4328d392605802de34406045b9701bb8',
	'a46ad0b9e7f771b6dca9e5a1496dca64',
	'd97173b555725243fea3fa3eff7529b6',
	'e7bb2a93c7c4a7fe26bf4c4272108e8c',
]

MIN_PROXY_LIFE_SPAN = 10
MAX_PROXY_LIFE_SPAN = 180

# indicate the purpose of current run
# RUN_PURPOSE = "READ_HTML" # read crawled files and parse saved html files
# RUN_PURPOSE = "GET_CHANNELS" # production run on Entrobus28
# RUN_PURPOSE = "PRODUCTION_RUN" # production run on Entrobus28
# RUN_PURPOSE = "CHECK_PROXY_IP"
RUN_PURPOSE = "SAVE_ONE_HTML"

SAVE_EVERY_RESPONSE = True

OVERWRITE_TODAY = ""
# OVERWRITE_TODAY = "20190430" # when RUN_PURPOSE is READ_HTML, you can overwrite "today"

if 0 < len( OVERWRITE_TODAY ) and "READ_HTML" == RUN_PURPOSE:
	today = OVERWRITE_TODAY

PIPELINE_TO_KAFKA = True

CRAWLED_DIR = os.path.join( PROJECT_PATH, SPIDER_NAME, "outputs", today )
SAVED_HTML = os.path.join( PROJECT_PATH, SPIDER_NAME, "outputs", f"{today}html" )
SAVED_GAODE_JASON = os.path.join( PROJECT_PATH, SPIDER_NAME, "outputs", f"{today}json" )

OVER70_LOG_FILENAME = f"over70_{today}.log"
