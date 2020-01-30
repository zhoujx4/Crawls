# coding: utf-8

import datetime
import os
import sys

PROJECT_DEBUG = True
PROJECT_PATH = os.getcwd()

today = datetime.datetime.now().strftime("%Y%m%d")
LOG_DIR = os.path.join( PROJECT_PATH, "logs" )
OUTPUT_FOLDER_NAME = "outputs"
INPUT_FOLDER_NAME = "inputs"
LOCATOR_PNG_FILE_NAME = "locator.png"
CRAWLED_DIR = os.path.join( PROJECT_PATH, OUTPUT_FOLDER_NAME, today )
LATEST_VERSION = "20190723"
BASE_URI = f"https://gss0.bdstatic.com/8bo_dTSlRsgBo1vgoIiO_jowehsv/tile/?qt=vtile&styles=pl&scaler=1&udt={LATEST_VERSION}"
LEVEL_Z = 16
BROWSER = "Chrome"
CITY_LNG_LAT_DICT = {
	# 114.706195, 23.740876
	# 111.838095, 21.578807
	"guangzhou":{
		"min_lng": "111.838095",
		"max_lng": "114.706195",
		"min_lat": "21.578807",
		"max_lat": "23.740876",
	},
}
CITY_LIST = ["guangzhou", ]
TILE_LNG_LAT_CSV = "tile_lng_lat.csv"

if not os.path.exists( LOG_DIR ):
	os.makedirs( LOG_DIR )
if not os.path.exists( CRAWLED_DIR ):
	os.makedirs( CRAWLED_DIR )
