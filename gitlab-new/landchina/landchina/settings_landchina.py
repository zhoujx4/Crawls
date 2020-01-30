# coding: utf-8

import datetime
import os
import sys

spider_name = "landchina"
today = datetime.datetime.now().strftime("%Y%m%d")

PROJECT_DEBUG = True
PROJECT_PATH = os.getcwd()
LOG_DIR = os.path.join( PROJECT_PATH, "logs" )
MAIN_LOG_FILE_NAME = f"{spider_name}_{today}.log"
OUTPUT_FOLDER_NAME = "outputs"
INPUT_FOLDER_NAME = "inputs"
CRAWLED_DIR = os.path.join( PROJECT_PATH, OUTPUT_FOLDER_NAME, today )
HTML_DIR = os.path.join( PROJECT_PATH, OUTPUT_FOLDER_NAME, f"{today}html" )
BROWSER = "ChromePC"
BASE_URI = "https://www.landchina.com/default.aspx"
MAXIMAL_REQUESTS = 50
MISSED_URL_FILE_NAME = f"missed_urls_{today}.log"

TABID_LIST = [
	# 263, # 结果公告
	226, # 供地计划 https://www.landchina.com/default.aspx?tabid=226
]

# TAB_QuerySubmitConditionData input框需要输入的内容
INPUT_KEYWORD_DICT = {
	226: ["广东省", "江苏省", ], # 需要爬取广东省（共22页）和江苏省（共18页）的供地计划
}

# 上面的所有keyword应该在下面字典内有英文翻译
KEYWORD_ENGLISH = {
	"广东省": "guangdong",
	"江苏省": "jiangsu",
}

if not os.path.exists( LOG_DIR ):
	os.makedirs( LOG_DIR )
if not os.path.exists( CRAWLED_DIR ):
	os.makedirs( CRAWLED_DIR )
if not os.path.exists( HTML_DIR ):
	os.makedirs( HTML_DIR )
	