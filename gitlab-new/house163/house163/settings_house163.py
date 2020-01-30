# coding: utf-8

import datetime
import os
import sys
import random

spider_name = "house163"

PROJECT_DEBUG = False
PROJECT_PATH = os.getcwd()

today = datetime.datetime.now().strftime("%Y%m%d")
LOG_DIR = os.path.join( PROJECT_PATH, "logs" )
MAIN_LOG_FILE_NAME = f"{spider_name}_{today}.log"
OUTPUT_FOLDER_NAME = "outputs"
INPUT_FOLDER_NAME = "inputs"
CRAWLED_DIR = os.path.join( PROJECT_PATH, OUTPUT_FOLDER_NAME, today )
EXCEL_DIR = os.path.join( PROJECT_PATH, OUTPUT_FOLDER_NAME, f"{today}excel" )
BROWSER = "ChromePC"
CITY_STRING = "广州市"
BASE_URI = "http://data.house.163.com/gz/housing/trend/product/todayflat/180/day/allproduct/1.html"
MAXIMAL_REQUESTS = random.randint(5,20)
MISSED_URL_FILE_NAME = f"missed_urls_{today}.log"

if not os.path.isdir( LOG_DIR ):
	os.makedirs( LOG_DIR )
if not os.path.isdir( CRAWLED_DIR ):
	os.makedirs( CRAWLED_DIR )
if not os.path.isdir( EXCEL_DIR ):
	os.makedirs( EXCEL_DIR )
	