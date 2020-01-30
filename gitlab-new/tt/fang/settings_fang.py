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
SPIDER_NAME = "fang"

DEFAULT_REQUEST_HEADERS = {
	'Accept': 'application/json,text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'en,zh-cn.utf-8',
	"Referer": "https://restapi.amap.com/v3/place/text",
}

DOWNLOADER_MIDDLEWARES = {
	'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware': 100,
}

today = datetime.datetime.now().strftime("%Y%m%d")
LOG_FILE = os.path.join( PROJECT_PATH, SPIDER_NAME, "logs", f"log_{SPIDER_NAME}" + today + ".log" )
LOG_LEVEL = "INFO"
LOG_ENCODING = "utf-8"
LOG_STDOUT = True


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"

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

# HTTPCACHE_ENABLED = False
HTTPCACHE_ENABLED = True
# HTTPCACHE_POLICY = DummyPolicy
# HTTPCACHE_STORAGE = FilesystemCacheStorage
HTTPCACHE_DIR = os.path.join( PROJECT_PATH, "cached/" )

ITEM_PIPELINES = {
	f'{SPIDER_NAME}.pipelines.FangPipeline': 300,
}

# if debugging, can overwrite the project settings
PROJECT_DEBUG = False
# PROJECT_DEBUG = True

# city names
# CITY_LIST = ['shaoyang', 'zhuzhou','changde', 'hengyang', 'gz', 'cs', 'fs',]
# shaoyang == 邵阳; zhuzhou == 株洲; changde == 常德; hengyang == 衡阳; gz == 广州; cs == 长沙; fs == 佛山
# yueyang == 岳阳; loudi == 娄底; chenzhou == 郴州
# CITY_LIST = ['shaoyang', 'zhuzhou', 'changde', 'hengyang', 'yueyang', 'loudi', 'chenzhou', 'cs', ]
# CITY_NAMES = ['shaoyang', 'zhuzhou', 'changde', 'hengyang', 'yueyang', 'loudi', 'chenzhou', 'changsha', ] # full city names for GaoDe

# CITY_LIST = ['hengyang', ]
# CITY_NAMES = ['hengyang', ]

# 'sz' == 深圳市, 'gz' == 广州市, 'fs' == 佛山市, 'dg' == 东莞市, 'zh' == 珠海市, 'zs' == 中山市, 'huizhou' == 惠州市, 'jm' == 江门市, 
# CITY_LIST = ['sz', 'gz', 'fs', 'dg', 'zh', 'zs', 'huizhou', 'jm', ]
# CITY_NAMES = ['shenzhen', 'guangzhou', 'foshan', 'dongguan', 'zhuhai', 'zhongshan', 'huizhou', 'jiangmen', ] # full city names for GaoDe

# shaoguan == 韶关, st == 汕头, zj == 湛江, zhaoqing == 肇庆, maoming == 茂名, meizhou == 梅州, shanwei == 汕尾, heyuan == 河源, 
# yangjiang == 阳江, qingyuan == 清远, chaozhou == 潮州, jieyang == 揭阳, yunfu == 云浮
# CITY_LIST = [ "shaoyang", "shaoguan", "st", "zj", "zhaoqing", "maoming", "meizhou", "shanwei", "heyuan", "yangjiang", "qingyuan", "chaozhou", "jieyang", "yunfu", ]
# CITY_NAMES = [ "shaoyang", "shaoguan", "shantou", "zhanjiang", "zhaoqing", "maoming", "meizhou", "shanwei", "heyuan", "yangjiang", "qingyuan", "chaozhou", "jieyang", "yunfu", ]

# 20190729
CITY_LIST = [ "cz", "yz", "suzhou", "wuxi", "ks", "nanjing", "sh", ]
CITY_NAMES = [ "changzhou", "yangzhou", "suzhou", "wuxi", "kunshan", "nanjing", "shanghai", ]

# 20190423接到通知，将8个城市缩减成为下面3个城市
# CITY_LIST = ['sz', 'gz', 'fs',]
# CITY_NAMES = ['shenzhen', 'guangzhou', 'foshan', ]
CRAWL_BATCHES = 2

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

# indicate the purpose of current run
# RUN_PURPOSE = "READ_HTML" # read crawled files and parse saved html files
RUN_PURPOSE = "PRODUCTION_RUN" # production run on Entrobus28

OVERWRITE_TODAY = ""
# OVERWRITE_TODAY = "20190430" # when RUN_PURPOSE is READ_HTML, you can overwrite "today"

if 0 < len( OVERWRITE_TODAY ) and "READ_HTML" == RUN_PURPOSE:
	today = OVERWRITE_TODAY

PIPELINE_TO_KAFKA = True

SAVE_EVERY_RESPONSE = True
CRAWLED_DIR = os.path.join( PROJECT_PATH, SPIDER_NAME, "outputs", today )
SAVED_DETAIL_HTML = os.path.join( PROJECT_PATH, SPIDER_NAME, "outputs", f"{today}html" )
SAVED_GAODE_JASON = os.path.join( PROJECT_PATH, SPIDER_NAME, "outputs", f"{today}json" )
