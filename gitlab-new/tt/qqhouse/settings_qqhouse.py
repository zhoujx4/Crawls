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
SPIDER_NAME = "qqhouse"

DEFAULT_REQUEST_HEADERS = {
	"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
	"Accept-Language": "zh-CN,zh;q=0.9",
	"Referer": "https://restapi.amap.com/v3/place/text",
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
CONCURRENT_REQUESTS_PER_IP = 1

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False
COOKIES_ENABLED = True

HTTPCACHE_ENABLED = False
# HTTPCACHE_ENABLED = True
# HTTPCACHE_POLICY = DummyPolicy
# HTTPCACHE_STORAGE = FilesystemCacheStorage
HTTPCACHE_DIR = os.path.join( PROJECT_PATH, "cached/" )

ITEM_PIPELINES = {
	f'{SPIDER_NAME}.pipelines.QqhousePipeline': 300,
}

# if debugging, can overwrite the project settings
PROJECT_DEBUG = False
# PROJECT_DEBUG = True

# list page numbers of different cities
CITY_PAGE_DICT = {
	# "gz": 173,
	# "fs": 254,
	# "sz": 563,
	# "dg":223, # 2227 records
	# "shaoguan": 12, # 118 records
	# "shaoyang": 15, #150 records
	"yueyang": 24, # 233 records
	"zhuzhou": 29, # 283 records
}

CITIES_FOR_CRAWLING = [
	# "gz",
	# "fs",
	# "sz",
	# "dg",
	# "shaoguan",
	# "shaoyang",
	"yueyang",
	"zhuzhou",
]

OUTPUT_FOLDER_NAME = "outputs"

MAXIMAL_LIST_PAGES = 1999 # if 0, no limits

PIPELINE_TO_KAFKA = True

SAVE_EVERY_RESPONSE = True
# SAVE_EVERY_RESPONSE = False

CRAWLED_DIR = os.path.join( PROJECT_PATH, SPIDER_NAME, OUTPUT_FOLDER_NAME, f"{today}crawled" )
SAVED_DETAIL_HTML = os.path.join( PROJECT_PATH, SPIDER_NAME, OUTPUT_FOLDER_NAME, f"{today}detail_html" )
SAVED_LIST_HTML = os.path.join( PROJECT_PATH, SPIDER_NAME, OUTPUT_FOLDER_NAME, f"{today}list_html" )

# indicate the purpose of current run
RUN_PURPOSE = "PRODUCTION_RUN" # production run on Entrobus28;
# RUN_PURPOSE = "REDO_MISSED_HOUSE_IDS"
# RUN_PURPOSE = "REDO_MISSED_PAGE_IDS"
# RUN_PURPOSE = "READ_CSV_TO_KAFKA"
DATES_TO_BE_READ = ["20190528",]

MISSED_ID_TXT = "missed_uris20190528guangzhou_batch01.txt" # uris including missed house ids
# MISSED_ID_TXT = "missed_pages.txt"

MAXIMAL_REQUEST_TIMES = [3, 6, 3, 15,]
