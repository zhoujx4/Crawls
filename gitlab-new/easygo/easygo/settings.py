#! /usr/local/bin/python3
# coding: utf-8
# __author__ = "Brady Hu" # https://zhuanlan.zhihu.com/p/30772570
# __date__ = 2017/10/16 16:11

import os
import sys
import datetime
import random

def get_city_and_input_file_name( input_path = None, task_file = "tasks.txt", debug = False ):
	"""
	return a tuple like ("yueyang_yueyanglouqu","yueyang2km_yueyanglouqu_with_zero.txt")
	"""
	returned_tuple = (None, None)
	if input_path is None:
		return returned_tuple
	city_list = []
	today = datetime.datetime.now().strftime("%Y%m%d")
	try:
		with open( os.path.join(input_path, task_file), 'r', encoding='utf-8') as f:
			rows = f.readlines()
			for index, item in enumerate( rows[1:] ):
				temp = tuple( item.strip().split(",") )
				if today == str(temp[0]):
					city_list.append( temp )
	except Exception as ex:
		return returned_tuple
	if 1 > len( city_list ):
		return returned_tuple

	if 1 > len( city_list ):
		return returned_tuple
	first_tuple = city_list[0]
	if 4 != len(first_tuple):
		return returned_tuple

	return ( first_tuple[2], first_tuple[3] )

#爬虫参数设置

rootpath = os.getcwd()
library_path = os.path.join( rootpath, "easygo" )
sys.path.append( library_path )

input_path = os.path.join( rootpath, "input" )
if not os.path.exists(input_path):
	os.makedirs(input_path)

debug = True

city, xy_name = get_city_and_input_file_name( input_path = input_path, debug = debug )
if xy_name is None or city is None:
	xy_name = "zhuzhou2km.txt" # 输入文件名称（经纬度）
	city = "zhuzhou" # 输入城市名称的拼音（全拼）

city_chinese_name_list = {
	"zhuzhou": "株洲",
	"shaoyang": "邵阳",
	"yueyang": "岳阳",
	"foshan": "佛山",
	"guangzhou": "广州",
	"shenzhen": "深圳",
}

# dragonfly proxy information
proxy_pwd = "00rPeu7HKvmu"
proxy_user = "JEVJ1625573267906612"

# 向代理request的最大次数
max_proxies = 20

# where to get new cookies? 
# 0 == from selenium webdriver; 1 == from input command; 2 == read from the cookies pool file
get_cookies_method = 2

# the browser that used for getting the cookie
browser = "Chrome"  # can only be in [ 'FireFox', 'IE', 'Chrome', 'Opera', '360', ]

# 每2次请求直接间隔最大秒数
delay_time = 0.6
minimal_delay = 0.2

# 当该次请求的服务器返回data为空的时候，而该经纬度为闹市区，则重复请求10次直到data不为空。
repeat_request_times_upon_empty_data = 3

# 当发现服务器返回的data数目大于30，就将这个经纬度标记为不能够为空的点。
threshold_to_turn1 = 30

# whether proxy will be used for crawling
use_proxy = False

filename_prefix = city

logfilepath = os.path.join( rootpath, "logs" )
if not os.path.exists( logfilepath ):
	os.makedirs( logfilepath )

jsonfilepath = os.path.join( rootpath, "jsons" )
if not os.path.exists( jsonfilepath ):
	os.makedirs( jsonfilepath )

save_every_response = True

sleeptime_between_cookies = 20 # in seconds

# request number for each cookie
# suggested 60 for proxy and 100 for direct visit
# as of 20190220, WeChat Server limits this to be 128
# fre = 95 # 110 # 80
fre = random.randint( 99, 110 )

# if crawling high population densitiy area for the first time, set this True
high_population_densitiy = False

#每次爬取方格的边长（单位：km）
edge = 2.6

#下面的参数不用设置
# https://zhidao.baidu.com/question/138957118823573885.html
lng_delta = 0.01167*edge
# 北纬30度，应该是0.010402707553*edge
# 北纬45度，应该是0.0127406627241*edge
# 北纬60度，应该是0.01801801801802*edge
# 赤道上经度每相差一度则相距111公里；北纬30度则是111乘以2分之根号3；
# 北纬45度则是111乘以2分之根号2；北纬60度则是111乘以1/2，即55.5公里
lat_delta = 0.009009009*edge # 每一纬度是111公里
