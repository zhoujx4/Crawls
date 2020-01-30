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
SPIDER_NAME = "traffic"

DEFAULT_REQUEST_HEADERS = {
	"Referer": "https://restapi.amap.com/v3/traffic/status/rectangle",
}

DOWNLOADER_MIDDLEWARES = {
	"scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware": 100,
}

today = datetime.datetime.now().strftime("%Y%m%d")
LOG_DIR = os.path.join( PROJECT_PATH, SPIDER_NAME, "logs" )
LOG_FILE = os.path.join( LOG_DIR, f"log_{SPIDER_NAME}{today}.log" ) # do NOT use overwrite_today here
LOG_LEVEL = "INFO"
LOG_ENCODING = "utf-8"
LOG_STDOUT = True

CITY_OR_AREA_NAME = "guangdong"
XY_RESPONSE_LOG_FILE_NAME = f"{CITY_OR_AREA_NAME}_seen_xy.log"

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
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16

# AMAP keys
AMAP_KEYS = [
	'4ebb849f151dddb3e9aab7abe6e344e2', # Peter的，每天30000次
	'470fdf698e3aab758d4cb026244f5194', # 下面5个都是曾基的同一个认证开发者账号，每天30000次
	'740f50c6fabd5801d0fad1cba62446d9',
	'4328d392605802de34406045b9701bb8',
	'a46ad0b9e7f771b6dca9e5a1496dca64',
	'd97173b555725243fea3fa3eff7529b6',
	'e7bb2a93c7c4a7fe26bf4c4272108e8c',
]

RANDOMIZE_DOWNLOAD_DELAY = False
if 0 < len(AMAP_KEYS):
	DOWNLOAD_DELAY = 60 / ( 45.0 * len(AMAP_KEYS) )
else:
	DOWNLOAD_DELAY = 60
CONCURRENT_REQUESTS_PER_IP = ( 45 * len(AMAP_KEYS) )

# https://github.com/scrapy/scrapy/issues/125

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False
COOKIES_ENABLED = True

HTTPCACHE_ENABLED = False
# HTTPCACHE_ENABLED = True
# HTTPCACHE_POLICY = DummyPolicy
# HTTPCACHE_STORAGE = FilesystemCacheStorage
HTTPCACHE_DIR = os.path.join( PROJECT_PATH, "cached/" )

# if debugging, can overwrite the project settings
PROJECT_DEBUG = False
# PROJECT_DEBUG = True

ITEM_PIPELINES = {
	f"{SPIDER_NAME}.pipelines.TrafficPipeline": 300,
}

SAVE_EVERY_RESPONSE = True
# SAVE_EVERY_RESPONSE = False

OUTPUT_FOLDER_NAME = "outputs"
OUTPUT_FILE_FORMAT = "json"			# shall be in query parameter list like: output=json

# indicate the purpose of current run
RUN_PURPOSE = "PRODUCTION_RUN" # production run on Entrobus28;
# RUN_PURPOSE = "READ_JSON_AND_WRITE_CSV"
# RUN_PURPOSE = "INITIALIZE_AMAP_XY"

# OVERWRITE_TODAY = "20190615"
OVERWRITE_TODAY = ""
if 0 < len( OVERWRITE_TODAY ) and "READ_JSON_AND_WRITE_CSV" == RUN_PURPOSE:
	today = OVERWRITE_TODAY

INPUT_XY_FILE_NAME = "data4cities_amap.txt"
INPUT_XY_FILE_PATH = os.path.join( PROJECT_PATH, SPIDER_NAME, INPUT_XY_FILE_NAME )
CRAWLED_DIR = os.path.join( PROJECT_PATH, SPIDER_NAME, OUTPUT_FOLDER_NAME, f"{today}" )
SAVED_JSON = os.path.join( PROJECT_PATH, SPIDER_NAME, OUTPUT_FOLDER_NAME, f"{today}json" )

BASE_URI = "https://restapi.amap.com/v3/traffic/status/rectangle"

PIPELINE_TO_KAFKA = True

# The following two are now placed in ./tt/settings.py
# CLUSTER_SERVERS_FOR_SPIDERS = [ "entrobus12", "entrobus28", "entrobus32", ]
# CLUSTER_SERVERS_FOR_KAFKA = [ "entrobus12", "entrobus28", "entrobus32", ]

# 5 minute between 2 adjacent reqests; 6 hours per crontab; 4 crontabs per day
MAXIMAL_REQUESTS_OF_ONE_CRONTAB_PROCESS = 71
INTERVAL_BETWEEN_REQUESTS = 300
