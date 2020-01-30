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
SPIDER_NAME = "directionbaidu"

DEFAULT_REQUEST_HEADERS = {
	"Referer": "http://api.map.baidu.com/direction/v2/driving",
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

HTTPCACHE_ENABLED = False
# HTTPCACHE_ENABLED = True
# HTTPCACHE_POLICY = DummyPolicy
# HTTPCACHE_STORAGE = FilesystemCacheStorage
HTTPCACHE_DIR = os.path.join( PROJECT_PATH, "cached/" )

# if debugging, can overwrite the project settings
PROJECT_DEBUG = False
# PROJECT_DEBUG = True

ITEM_PIPELINES = {
	f"{SPIDER_NAME}.pipelines.DirectionbaiduPipeline": 300,
}

SAVE_EVERY_RESPONSE = True
# SAVE_EVERY_RESPONSE = False

OUTPUT_FOLDER_NAME = "outputs"
OUTPUT_FILE_FORMAT = "json"			# shall be in query parameter list like: output=json

# indicate the purpose of current run
RUN_PURPOSE = "PRODUCTION_RUN" # production run on Entrobus28;
# RUN_PURPOSE = "READ_JSON_AND_WRITE_CSV"

# OVERWRITE_TODAY = "20190615"
OVERWRITE_TODAY = ""
if 0 < len( OVERWRITE_TODAY ) and "READ_JSON_AND_WRITE_CSV" == RUN_PURPOSE:
	today = OVERWRITE_TODAY

CRAWLED_DIR = os.path.join( PROJECT_PATH, SPIDER_NAME, OUTPUT_FOLDER_NAME, f"{today}crawled" )
SAVED_JSON = os.path.join( PROJECT_PATH, SPIDER_NAME, OUTPUT_FOLDER_NAME, f"{today}json" )

BASE_URI = "http://api.map.baidu.com/direction/v2/driving"

PIPELINE_TO_KAFKA = True

# The following two are now placed in ./tt/settings.py
# CLUSTER_SERVERS_FOR_SPIDERS = [ "entrobus12", "entrobus28", "entrobus32", ]
# CLUSTER_SERVERS_FOR_KAFKA = [ "entrobus12", "entrobus28", "entrobus32", ]

MAXIMAL_REQUESTS_OF_ONE_CRONTAB_PROCESS = 23
INTERVAL_BETWEEN_REQUESTS = 300
