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
SPIDER_NAME = "bus8684"

DEFAULT_REQUEST_HEADERS = {
	"Referer": "https://guangzhou.8684.cn/",
}

DOWNLOADER_MIDDLEWARES = {
	"scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware": 100,
}

today = datetime.datetime.now().strftime("%Y%m%d")
LOG_DIR = os.path.join( PROJECT_PATH, SPIDER_NAME, "logs" )
LOG_FILE = os.path.join( LOG_DIR, f"log_{SPIDER_NAME}{today}.log" )
LOG_LEVEL = "INFO"
LOG_ENCODING = "utf-8"
LOG_STDOUT = True

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"

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

RANDOMIZE_DOWNLOAD_DELAY = False
# DOWNLOAD_DELAY = 60
CONCURRENT_REQUESTS_PER_IP = 4
# https://github.com/scrapy/scrapy/issues/125

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False
COOKIES_ENABLED = True

# HTTPCACHE_ENABLED = False
HTTPCACHE_ENABLED = True
# HTTPCACHE_POLICY = DummyPolicy
# HTTPCACHE_STORAGE = FilesystemCacheStorage
HTTPCACHE_DIR = os.path.join( PROJECT_PATH, "cached/" )

# if debugging, can overwrite the project settings
PROJECT_DEBUG = False
# PROJECT_DEBUG = True

ITEM_PIPELINES = {
	f'{SPIDER_NAME}.pipelines.Bus8684Pipeline': 300,
}

SAVE_EVERY_RESPONSE = True
# SAVE_EVERY_RESPONSE = False

OUTPUT_FOLDER_NAME = "outputs"

CRAWLED_DIR = os.path.join( PROJECT_PATH, SPIDER_NAME, OUTPUT_FOLDER_NAME, f"{today}" )
SAVED_HTML = os.path.join( PROJECT_PATH, SPIDER_NAME, OUTPUT_FOLDER_NAME, f"{today}html" )
SAVED_GAODE_JASON = os.path.join( PROJECT_PATH, SPIDER_NAME, OUTPUT_FOLDER_NAME, f"{today}json" )

BASE_URI = "8684.cn"

PIPELINE_TO_KAFKA = True

# indicate the purpose of current run
RUN_PURPOSE = "PRODUCTION_RUN" # production run on Entrobus28 or 32;
# RUN_PURPOSE = "READ_HTML"

BUS8684_CITY_LIST = [
	# "shenzhen",
	# "guangzhou",
	# "foshan",
	# "dongguan",
	# "shaoguan",
	# "zhuhai",
	# "zhongshan",
	# "huizhou",
	# "jiangmen",
	# "yueyang",
	# "shaoyang",
	# "zhuzhou",
	# "changde",
	"loudi",
]
AMAP_CITY_LIST = [
	# "shenzhen",
	# "guangzhou",
	# "foshan",
	# "dongguan",
	# "shaoguan",
	# "zhuhai",
	# "zhongshan",
	# "huizhou",
	# "jiangmen",
	# "yueyang",
	# "shaoyang",
	# "zhuzhou",
	# "changde",
	"loudi",
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

AMAP_POI_TYPE = {
	150700:	"交通设施服务,公交车站,公交车站相关",
	150701:	"交通设施服务,公交车站,旅游专线车站",
	150702:	"交通设施服务,公交车站,普通公交站",
	150703:	"交通设施服务,公交车站,机场巴士",
	150800:	"交通设施服务,班车站,班车站",
}
