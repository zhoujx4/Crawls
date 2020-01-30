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
SPIDER_NAME = "poibaidu"

DEFAULT_REQUEST_HEADERS = {
	"Referer": "http://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-placeapi",
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

BAIDU_AK = [
	# "ntGWw6W7UCZ7KCX5hBQMj8yUVAPezwGp",			# provided by 袁小婷
	# "FGu8zzKVqOCdOwQF33SzA451IrSvV4ub",			# provided by 曾基 # 210 APP IP校验失败 or 211 APP SN校验失败
	# "18gDjrBd3Pzd8DyY8yrvkwoesG8IV7pM",			# Peter's opencv
	# "tCZvfo492TCBv6rUy7yKoUaZGi4Pu48b",			# provided by 莫璐因
	"6KOpBlVG6BLzK9IlxDY5bklPUlubgUmD",			# provided by 谭湘龙
	# "v4IuSCGf97epv4IulTj6oXnadZizOalU",			# provided by 刘剑诗
]

RANDOMIZE_DOWNLOAD_DELAY = False
if 0 < len(BAIDU_AK):
	DOWNLOAD_DELAY = 60 / ( 45.0 * len(BAIDU_AK) )
else:
	DOWNLOAD_DELAY = 60
CONCURRENT_REQUESTS_PER_IP = ( 45 * len(BAIDU_AK) )
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
	f'{SPIDER_NAME}.pipelines.PoibaiduPipeline': 300,
}

SAVE_EVERY_RESPONSE = True
# SAVE_EVERY_RESPONSE = False

INPUT_FOLDER_NAME = "inputs"
OUTPUT_FOLDER_NAME = "outputs"
QUERY_CLASSIFICATION_FILENAME = "baidu_poi_classification.txt"
OUTPUT_FILE_FORMAT = "json"			# shall be in query parameter list like: output=json

CRAWLED_DIR = os.path.join( PROJECT_PATH, SPIDER_NAME, OUTPUT_FOLDER_NAME, f"{today}crawled" )
SAVED_JSON = os.path.join( PROJECT_PATH, SPIDER_NAME, OUTPUT_FOLDER_NAME, f"{today}json" )

BASE_URI = "https://api.map.baidu.com/place/v2/search"

QUERY_TYPE = 3
# 1 means: "http://api.map.baidu.com/place/v2/search?query=ATM机&tag=银行&region=北京&output=json&ak=您的ak" # requesting pois in one city
# 2 means: "http://api.map.baidu.com/place/v2/search?query=银行&location=39.915,116.404&radius=2000&output=xml&ak=您的密钥" # requesting pois in one circle area
# 3 means: "http://api.map.baidu.com/place/v2/search?query=银行&bounds=39.915,116.404,39.975,116.414&output=json&ak={您的密钥}" # requesting pois in one rectangle area
# 4 means: "http://api.map.baidu.com/place/v2/detail?uid=435d7aea036e54355abbbcc8&output=json&scope=2&ak=您的密钥" # requesting pois at one location with detailed address

QUERY_TYPE3EDGE = 1.1

RUN_PURPOSE_BOUT = 2

# http://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-placeapi
BAIDU_STATUS_CODE = {
	"0": "ok;正常;服务请求正常召回",
	"2": "Parameter Invalid;请求参数非法;必要参数拼写错误或漏传（如query和tag请求中均未传入）",
	"3": "Verify Failure;权限校验失败",
	"4": "Quota Failure;配额校验失败;服务当日调用次数已超限，请前往API控制台提升（请优先进行开发者认证）",
	"5": "AK Failure;ak不存在或者非法",
	"210": "APP IP校验失败",
	"211": "APP SN校验失败",
	"302": "天配额超限，限制访问",
}

DATABASE_ENGLISH_CATEGORY_TABLE = {
	# Level 1
	"美食": "cater",
	"酒店": "hotel",
	"购物": "shopping",
	"生活服务": "life", # 20190605 changed from "services",
	"丽人": "beauty",
	"旅游景点": "scope", # 20190605 changed from "tourist_attractions",
	"休闲娱乐": "entertainment", # 20190605 did not change, but mosts are life, hotel or so
	"运动健身": "sports", # 20190605 changed from "sports_fitness". mosts are scope
	"教育培训": "education",
	"文化传媒": "culturals", # 20190605 did not change, but mosts are scope or so
	"医疗": "hospital",
	"汽车服务": "automobile", # 20190605 changed from "automobile_services",
	"交通设施": "transportation", # 20190605 did not change, but mosts are life or so
	"金融": "finance", # 20190605 did not change, but mosts are life or so
	"房地产": "house",
	"公司企业": "enterprise",
	"政府机构": "administrations", # 20190605 did not change, but mosts are life, enterprise or so
	"出入口": "entrance", # 20190605 changed from "entrance_and_exit". mosts are life
	"自然地物": "natural", # 20190605 changed from "natural_features". mosts are scope
	"道路": "road", # 20190605 newly found, including 高速公路、路口
	"行政地标": "district", # 20190605 newly found, including 村庄、地级市
	"门址": "gate", # 20190605 newly found, including 门址点

	# Level 2
	"中餐厅": "cater___100",
	"外国餐厅": "cater___101",
	"小吃快餐店": "cater___102",
	"蛋糕甜品店": "cater___103",
	"咖啡厅": "cater___104",
	"茶座": "cater___105",
	"酒吧": "cater___106",

	"星级酒店": "hotel___200",
	"快捷酒店": "hotel___201",
	"公寓式酒店": "hotel___202",

	"购物中心": "shopping___300",
	"百货商场": "shopping___301",
	"超市": "shopping___302",
	"便利店": "shopping___303",
	"家居建材": "shopping___304",
	"家电数码": "shopping___305",
	"商铺": "shopping___306",
	"集市": "shopping___307",
	"市场": "shopping___309",

	"通讯营业厅": "life___400",
	"邮局": "life___401",
	"物流公司": "life___402",
	"售票处": "life___403",
	"洗衣店": "life___404",
	"图文快印店": "life___405",
	"照相馆": "life___406",
	"房产中介机构": "life___407",
	"公用事业": "life___408",
	"维修点": "life___409",
	"家政服务": "life___410",
	"殡葬服务": "life___411",
	"彩票销售点": "life___412",
	"宠物服务": "life___413",
	"报刊亭": "life___414",
	"公共厕所": "life___415",

	"美容": "beauty___500",
	"美发": "beauty___501",
	"美甲": "beauty___502",
	"美体": "beauty___503",

	"公园": "scope___600",
	"动物园": "scope___601",
	"植物园": "scope___602",
	"游乐园": "scope___603",
	"博物馆": "scope___604",
	"水族馆": "scope___605",
	"海滨浴场": "scope___606",
	"文物古迹": "scope___607",
	"教堂": "scope___608",
	"风景区": "scope___609",
	"景点": "scope___611",
	"寺庙": "scope___612",

	"度假村": "entertainment___700",
	"农家院": "entertainment___701",
	"电影院": "entertainment___702",
	"KTV": "entertainment___703",
	"剧院": "entertainment___704",
	"歌舞厅": "entertainment___705",
	"网吧": "entertainment___706",
	"游戏场所": "entertainment___707",
	"洗浴按摩": "entertainment___708",
	"休闲广场": "entertainment___709",

	"体育场馆": "sports___800",
	"极限运动场所": "sports___801",
	"健身中心": "sports___802",

	"高等院校": "education___900",
	"中学": "education___901",
	"小学": "education___902",
	"幼儿园": "education___903",
	"成人教育": "education___904",
	"亲子教育": "education___905",
	"特殊教育学校": "education___906",
	"留学中介机构": "education___907",
	"科研机构": "education___908",
	"培训机构": "education___909",
	"图书馆": "education___910",
	"科技馆": "education___911",

	"新闻出版": "culturals___1000",
	"广播电视": "culturals___1001",
	"艺术团体": "culturals___1002",
	"美术馆": "culturals___1003",
	"展览馆": "culturals___1004",
	"文化宫": "culturals___1005",

	"综合医院": "hospital___1100",
	"专科医院": "hospital___1101",
	"诊所": "hospital___1102",
	"药店": "hospital___1103",
	"体检机构": "hospital___1104",
	"疗养院": "hospital___1105",
	"急救中心": "hospital___1106",
	"疾控中心": "hospital___1107",
	"医疗保健": "hospital___1112",
	"医疗器械": "hospital___1113",

	"汽车销售": "automobile___1200",
	"汽车维修": "automobile___1201",
	"汽车美容": "automobile___1202",
	"汽车配件": "automobile___1203",
	"汽车租赁": "automobile___1204",
	"汽车检测场": "automobile___1205",

	"飞机场": "transportation___1300",
	"火车站": "transportation___1301",
	"地铁站": "transportation___1302",
	"地铁线路": "transportation___1303",
	"长途汽车站": "transportation___1304",
	"公交车站": "transportation___1305",
	"公交线路": "transportation___1306",
	"港口": "transportation___1307",
	"停车场": "transportation___1308",
	"加油加气站": "transportation___1309",
	"服务区": "transportation___1310",
	"收费站": "transportation___1311",
	"桥": "transportation___1312",
	"充电站": "transportation___1313",
	"路侧停车位": "transportation___1314",

	"银行": "finance___1400",
	"ATM": "finance___1401",
	"信用社": "finance___1402",
	"投资理财": "finance___1403",
	"典当行": "finance___1404",

	"写字楼": "house___1500",
	"住宅区": "house___1501",
	"宿舍": "house___1502",
	"内部楼栋": "house___1504",

	"公司": "enterprise___1600",
	"园区": "enterprise___1601",
	"农林园艺": "enterprise___1602",
	"厂矿": "enterprise___1603",

	"中央机构": "administrations___1700",
	"各级政府": "administrations___1701",
	"行政单位": "administrations___1702",
	"公检法机构": "administrations___1703",
	"涉外机构": "administrations___1704",
	"党派团体": "administrations___1705",
	"福利机构": "administrations___1706",
	"政治教育机构": "administrations___1707",
	"居民委员会": "administrations___1709",
	"民主党派": "administrations___1710",
	"社会团体": "administrations___1711",

	"高速公路出口": "entrance___1800",
	"高速公路入口": "entrance___1801",
	"机场出口": "entrance___1802",
	"机场入口": "entrance___1803",
	"车站出口": "entrance___1804",
	"车站入口": "entrance___1805",
	"门": "entrance___1806",
	"停车场出入口": "entrance___1807",

	"岛屿": "natural___1900",
	"山峰": "natural___1901",
	"水系": "natural___1902",

	"高速公路": "road___2000",
	"路口": "road___2001",

	"村庄": "district___2100",
	"地级市": "district___2101",

	"门址点": "gate___2200",

	# "其他":"other", # tested on 20190605, we cannot use this as query, nor as tag!
} # after checking "detail_info" in json file, the English name of "type" has little help.

NEED_LEVELS = 2
# 1 == NEED_LEVELS will ONLY request classification_dict.keys()
# 2 == NEED_LEVELS will ONLY request classification_dict.values()
# 3 == NEED_LEVELS will request both

PIPELINE_TO_KAFKA = True

MAXIMAL_REQUEST_TIMES = [3, 6, 3, 9,]

# indicate the purpose of current run
RUN_PURPOSE = "PRODUCTION_RUN" # production run on Entrobus28;
# RUN_PURPOSE = "REDO_OVER400_POIS"

CITY_LIST = [
	# "guangzhou",
	# "foshan",
	"shenzhen",
	# "jiangmen",
	# "zhongshan",
	# "zhuhai",
	# "dongguan",
	# "huizhou",
]
