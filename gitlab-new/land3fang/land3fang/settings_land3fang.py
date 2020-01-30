# coding: utf-8

import datetime
import os
import sys

PROJECT_DEBUG = False
PROJECT_PATH = os.getcwd()

today = datetime.datetime.now().strftime("%Y%m%d")
LOG_DIR = os.path.join( PROJECT_PATH, "logs" )
OUTPUT_FOLDER_NAME = "outputs"
INPUT_FOLDER_NAME = "inputs"
CRAWLED_DIR = os.path.join( PROJECT_PATH, OUTPUT_FOLDER_NAME, today )
HTML_DIR = os.path.join( PROJECT_PATH, OUTPUT_FOLDER_NAME, f"{today}html" )
BROWSER = "ChromePC"

if not os.path.exists( LOG_DIR ):
	os.makedirs( LOG_DIR )
if not os.path.exists( CRAWLED_DIR ):
	os.makedirs( CRAWLED_DIR )
if not os.path.exists( HTML_DIR ):
	os.makedirs( HTML_DIR )
	