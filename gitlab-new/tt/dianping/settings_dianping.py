# -*- coding: utf-8 -*-

import datetime
import os
import scrapy
# from scrapy.extensions.httpcache import DummyPolicy
# from scrapy.extensions.httpcache import FilesystemCacheStorage

PROJECT_PATH = os.getcwd()
SPIDER_NAME = "dianping"

LOG_FILE = os.path.join( PROJECT_PATH, SPIDER_NAME, "logs", f"log_{SPIDER_NAME}" + datetime.datetime.now().strftime("%Y%m%d") + ".log" )
LOG_LEVEL = "INFO"

DEFAULT_REQUEST_HEADERS = {
	'Accept': 'text/html, application/xhtml+xml, image/jxr, */*',
	'Accept-Encoding': 'gzip, deflate',
	'Accept-Language': 'zh-CN',
	"Referer": "http://www.dianping.com",
}

DOWNLOADER_MIDDLEWARES = {
	'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware': 100,
}

# COOKIES_ENABLED = True
COOKIES_ENABLED = False

# AUTOTHROTTLE_ENABLED = True
# DOWNLOAD_DELAY = 1  # in seconds
# https://blog.csdn.net/weixin_42260204/article/details/81096459

# this cache is no longer useful, www.dianping.com can ONLY be crawled by fiddler
HTTPCACHE_ENABLED = True
# HTTPCACHE_POLICY = DummyPolicy
# HTTPCACHE_STORAGE = FilesystemCacheStorage
HTTPCACHE_DIR = os.path.join( PROJECT_PATH, "cached/" ) # + datetime.datetime.now().strftime("%Y%m%d") + "/"

ITEM_PIPELINES = {
	f'{SPIDER_NAME}.pipelines.DianpingPipeline': 300,
}

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
# 'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 543,
# DOWNLOADER_MIDDLEWARES = {
# 	f"{SPIDER_NAME}.middlewares.ProxyDownloaderMiddleware": 543,
# }

# HTTPPROXY_ENABLED = True
# HTTPPROXY_AUTH_ENCODING = 'utf-8'
# to use proxy, need to set the environmental parameters
# http_proxy
# https_proxy
# no_proxy

# for distributed crawls and ftp/socket item pipelines
# SOCKET_HOST = 'localhost'
# SOCKET_PORT = 21567
# SOCKET_BUFSIZ = 524288 # 500kb

# DISTRIBUTED_TARGET_RULE = 1
# DISTRIBUTED_BATCH_SIZE = 2000
# DISTRIBUTED_TARGET_HOSTS = [
# 	"scrapyd1:6800",
# 	"scrapyd2:6800",
# 	"scrapyd3:6800",
# ]
# DISTRIBUTED_TARGET_FEED_URL = ("ftp://anonymous@spark/" "%(batch)s_%(name)s_%(time)s.jl")

# SPIDER_MIDDLEWARES = {
# 	'tt.middlewares.Distributed': 100,
# }

# if channel files are older than 10 days, then update them
CHANNEL_FILE_UPDATE_FREQUENCY = 10

# file folder name for this spider ONLY:
SVG_TEXT_CSS = 'svgtextcss'

# default spider directories; can overwrite default project directories here
# CRAWLED_DIR = 'crawled'
# SAVED_DETAIL_HTML = 'detail_html'
# SAVED_LIST_HTML = 'list_html'

# if debugging, can overwrite the project settings
# PROJECT_DEBUG = False
# PROJECT_DEBUG = True

# We do not connect to a database, just use setting:
DATABASE_COMMON_CHANNEL_LIST_TABLE = ['ch10', 'ch15', 'ch20', 'ch25', 'ch30', 'ch45', 'ch50', 'ch65', 'ch75', 'ch80', 'ch85', 'ch95', ]
# these channels represent channels of 美食，娱乐会所/KTV，购物，电影院，演出/剧院，运动场所，丽人，爱车，学习培训，生活服务，医疗健康，宠物
# 'ch70', 亲子
# 'ch90', 家装		a newly added channel
# 对于一个新channel需要检查dianping.py的255行；"//div[@id='shop-all-list']/ul/li"；
# level2categories_a = response.xpath("//div[@id='classfy']/a")
# review_number_a = one_li.xpath("./div[@class='txt']/div[@class='comment']/a[@class='review-num']")
# comment_score_span = one_li.xpath("./div[@class='txt']/span[@class='comment-list']/span")

# On 20190505, www.dianping.com releases this new anticrawl method:
# These are all unicode characters; these include Chinese, no just digits
DATABASE_ANTICRAWL20190505_TABLE = {
	# "\ue573": "1",
	# "\ue3a3": "2",
	# "\uf759": "3",
	# "\uf831": "4",
	# "\ue2ba": "5",
	# "\ue96b": "6",
	# "\ue7d4": "7",
	# "\uf8d6": "8",
	# "\ueb25": "9",
	# "\uee53": "0",

	"e573": "1",
	"e3a3": "2",
	"f759": "3",
	"f831": "4",
	"e2ba": "5",
	"e96b": "6",
	"e7d4": "7",
	"f8d6": "8",
	"eb25": "9",
	"ee53": "0",
}

DATABASE_MERCHANT_STAR_LEVEL_TABLE = {
	0: '该商户暂无星级',
	10: '一星商户',
	15: '准二星商户',
	20: '二星商户',
	25: '准三星商户',
	30: '三星商户',
	35: '准四星商户',
	40: '四星商户',
	45: '准五星商户',
	50: '五星商户',
}

# 20190509 district name dictionary was added
DATABASE_CITY_DISTRICT_TABLE = {
	'guangzhou': {
		'r24': "越秀区",
		'r26': "荔湾区",
		'r22': "天河区",
		'r25': "海珠区",
		'r1549': "黄埔区",
		'r621': "番禺区",
		'r27': "白云区",
		'r1554': "增城区",
		'r1552': "花都区",
		'c4459': "南沙区",
		'c413': "从化区",
	},
}

DATABASE_LEVEL2NAME_TABLE = {
	# ch20
	"g119": "综合商场",
	"g33943": "服装",
	"g33944": "鞋靴",
	"g34124": "杂货礼品",
	"g120": "其他服装鞋包",
	"g121": "运动户外",
	"g187": "超市/便利店",
	"g235": "药店",
	"g123": "化妆品",
	"g128": "眼镜店",
	"g125": "母音购物",
	"g124": "数码产品",
	"g33760": "烟酒茶叶",
	"g127": "书店音像",
	"g126": "家居建材",
	"g2714": "水果生鲜",
	"g34149": "植物花卉",
	"g34269": "配饰",
	"g33905": "箱包",
	"g6716": "钟表",
	"g33858": "居家日用",
	"g32698": "古玩字画",
	"g2776": "批发店",
	"g129": "特色集市",
	"g26101": "办公/文化用品",
	"g33906": "内衣",
	"g34208": "快时尚",
	"g34204": "自行/电动车及配件",
	"g34114": "乐器",
	"g130": "折扣店",
	"g32720": "奢侈品",
	"g34207": "轻奢",
	"g32739": "免税店",
	"g131": "更多购物场所",

	# ch15
	"g135": "KTV",
	"g2892": "娱乐会所",
	"g2894": "录音棚",

	# ch30
	"g141": "按摩/足疗",
	"g140": "洗浴/汗蒸",
	"g133": "酒吧",
	"g2636": "运动健身",
	"g134": "茶馆",
	"g2754": "密室",
	"g34089": "团建拓展",
	"g20038": "采摘/农家乐",
	"g137": "游乐游艺",
	"g144": "DIY手工坊",
	"g20041": "私人影院",
	"g20040": "轰趴馆",
	"g20042": "网吧/电竞",
	"g33857": "VR",
	"g6694": "桌面游戏",
	"g32732": "棋牌室",
	"g142": "文化艺术",
	"g34090": "新奇体验",
}

# indicate the purpose of current run
RUN_PURPOSE = "PARSE_FIDDLER" # whether this run is reading html files generated from fiddler
# RUN_PURPOSE = "PARSE_DETAILED_HOTEL" # the detailed pages of hotel channel have been crawled and saved by fiddler. Now we are parsing these html files

MOVE_FIDDLER_HTML_FILE = True
