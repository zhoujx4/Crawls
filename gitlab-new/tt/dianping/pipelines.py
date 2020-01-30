# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import time
import sys
import os
import json
import pandas
import datetime
import csv
import re

import scrapy
from scrapy.exceptions import DropItem
from scrapy.utils.request import referer_str
from scrapy.loader import ItemLoader

from dianping.items import DianpingItem
from dianping.items import DianpingListItem

class DianpingPipeline(object):
	csv_file = None
	csv_list_file = None
	csv_category_file = None
	csv_crawled_channel_file = None
	csv_svg_css_file = None
	crawled_dir = None
	svgtextcss_dir = None
	debug = None

	def get_items_and_keys(self, item=None, excluded_list=[]):
		item_list = []
		all_keys = []
		if item is None:
			return all_keys, item_list
		for index, one in enumerate( item ):
			if one not in excluded_list:
				all_keys.append( one )
				if 0 == len(item[one]):
					item_list.append("")
				elif 1 == len(item[one]):
					item_list.append( item[one][0] )
				else:
					item_list.append( item[one] )
		return all_keys, item_list
	
	def process_item(self, item, spider):
		project_path = spider.settings.get('PROJECT_PATH')
		spider_name = spider.name
		now = datetime.datetime.now()
		today = now.strftime("%Y%m%d")
		item_list = []
		all_keys = []
		targeted_page = ''
		self.get_crawled_dir(spider = spider)
		self.get_svgtextcss_dir(spider = spider)
		
		if self.debug is None:
			self.debug = spider.settings.get( name = 'PROJECT_DEBUG', default=False )

		for index, one in enumerate( item ):
			if 'targeted_page' == one and 1 == len(item['targeted_page']):
				targeted_page = str(item['targeted_page'][0])
		if 'list2' == targeted_page:
			excluded_list = ['css_url', 'shop_list', 'category_id', 'category_list', 'targeted_page', 'decoded_shop_dict', ]
			# get item_list and all_keys, these are housekeeping fields like url, project, date, and so on
			all_keys, item_list = self.get_items_and_keys(item=item, excluded_list=excluded_list)

			# write to the channel csv file (city_channel_yyyymmdd.csv) in crawled folder
			existance = False
			category_id = item['category_id'][0] if isinstance(item['category_id'],list) else item['category_id']
			category_id_city_list = category_id.split("___")
			if 2 == len( category_id_city_list ):
				city = category_id_city_list[0]
				channel = category_id_city_list[1]
				existance = self.check_channel_file(city= city, channel=channel, spider=spider)
			if not existance:
				if self.csv_category_file is None:
					self.csv_category_file = os.path.join( self.crawled_dir, f'{city}_{channel}_{today}.csv' )
				if 'category_list' in item.keys():
					for one_category in item['category_list']:
						all_keys2, item_list2 = self.get_items_and_keys(item=one_category, excluded_list=[])
						all_keys2.extend(all_keys)
						item_list2.extend(item_list)
						self.write_one_row(item_list=item_list2, file_path=self.csv_category_file, all_keys=all_keys2, no_json_dumps=True, item=item, spider=spider)

			# get decoded shop fields
			decoded_shop_dict = item['decoded_shop_dict']
			if not isinstance(decoded_shop_dict, dict):
				decoded_shop_dict = decoded_shop_dict[0]

			# append to the shop list csv file (city_channel_shop_list.csv) in crawled folder
			if self.csv_list_file is None:
				self.csv_list_file = os.path.join( self.crawled_dir, f'{city}_{channel}_shop_list.csv' )
			for one_shop in item['shop_list']:
				all_keys2, item_list2 = self.get_items_and_keys(item=one_shop, excluded_list=[])
				shop_id = one_shop['shop_id']
				this_shop_decoded = decoded_shop_dict[shop_id]
				all_keys3 = this_shop_decoded.keys()
				item_list3 = this_shop_decoded.values()
				all_keys2.extend(all_keys3)
				item_list2.extend(item_list3)
				all_keys2.extend(all_keys)
				item_list2.extend(item_list)
				self.write_one_row(item_list=item_list2, file_path=self.csv_list_file, all_keys=all_keys2, no_json_dumps=True, item=item, spider=spider)

			# append to city_svg_css_log.csv in svgtextcss folder
			if self.csv_svg_css_file is None:
				self.csv_svg_css_file = os.path.join( self.svgtextcss_dir, f'{city}_svg_css_log.csv' )
			css_url = item['css_url'][0] if isinstance(item['css_url'],list) else item['css_url']
			css_filename = css_url.split('/')
			this_url = item['url'][0] if isinstance(item['url'],list) else item['url']
			crawled_date = item['date'][0] if isinstance(item['date'],list) else item['date']
			if 0 < len(css_filename):
				css_filename = css_filename[-1]
			all_keys3 = ['css_url', 'css_filename', 'url', 'date',]
			item_list3 = [ css_url, css_filename, this_url, crawled_date ]
			self.write_one_row(item_list=item_list3, file_path=self.csv_svg_css_file, all_keys=all_keys3, no_json_dumps=True, item=item, spider=spider)

			# write to this channel in this city csv file to including the total pages
			# 'http://www.dianping.com/shaoyang/ch10/g113',
			# 'http://www.dianping.com/shaoyang/ch10/g113p2',
			if self.csv_crawled_channel_file is None:
				self.csv_crawled_channel_file = os.path.join( self.crawled_dir, f'{city}_{channel}_crawled.csv' )
			self.write_one_row(item_list=item_list, file_path=self.csv_crawled_channel_file, all_keys=all_keys, no_json_dumps=True, item=item, spider=spider)
		
		if targeted_page in [ 'detailed', 'no_hits', ]:
			all_keys, item_list = self.get_items_and_keys(item=item, excluded_list=[])
			if self.csv_file is None:
				csv_filename = os.path.join( self.crawled_dir, f'dianping{today}.csv' )
				self.csv_file = csv_filename
			self.write_one_row(item_list=item_list, file_path=self.csv_file, all_keys=all_keys, no_json_dumps=True, item=item, spider=spider)
		
		return item

	def get_crawled_dir(self, spider = None):
		if self.crawled_dir is None:
			root_path = spider.settings.get( name='PROJECT_PATH' )
			crawled = spider.settings.get( name='CRAWLED_DIR', default='crawled' )
			spider_name = spider.settings.get( name='SPIDER_NAME', default='dianping' )
			self.crawled_dir = os.path.join( root_path, spider_name, crawled )

	def get_svgtextcss_dir(self, spider = None):
		if self.svgtextcss_dir is None:
			root_path = spider.settings.get( name='PROJECT_PATH' )
			spider_name = spider.settings.get( name='SPIDER_NAME', default='dianping' )
			svg_text_css = spider.settings.get( name='SVG_TEXT_CSS', default='svgtextcss' )
			self.svgtextcss_dir = os.path.join( root_path, spider_name, svg_text_css )

	def check_channel_file(self, city="", channel="", spider=None):
		if city is None or 1 > len(city) or channel is None or 1 > len(channel) or spider is None:
			return False
		self.get_crawled_dir(spider = spider)

		channel_file_update_frequency = spider.settings.get( name='CHANNEL_FILE_UPDATE_FREQUENCY', default='10' )
		file_list = os.listdir( self.crawled_dir )
		file_name_prefix = f"{city}_{channel}"
		last_date = 0
		for i in range(0,len(file_list)):
			channel_pos = file_list[i].find( file_name_prefix )
			if -1 < channel_pos:
				temp_list = file_list[i].split('_')
				if 2 < len( temp_list ):
					last_date_list = temp_list[2].split('.')
					searchObj = re.search( r'(\d)+', last_date_list[0], re.M|re.I )
					if searchObj is not None:
						start = searchObj.span()[0]
						end = searchObj.span()[1]
						if end - start == len( last_date_list[0] ) and last_date < int(last_date_list[0]):
							last_date = int( last_date_list[0] )
		
		now = datetime.datetime.now()
		today = now.strftime("%Y%m%d")
		if int(channel_file_update_frequency) < int(today) - last_date:
			return False
		return True
		
	def write_one_row(self, item_list=[], file_path = "", all_keys=[], no_json_dumps=False, item=None, spider=None):
		has_no_file = False
		if not os.path.isfile( file_path ):
			has_no_file = True
		try:
			with open( file_path, 'a', encoding='utf-8', newline="") as f:
				writer = csv.writer(f)
				if has_no_file:
					writer.writerow( all_keys )
				if self.debug or no_json_dumps:
					writer.writerow( item_list )
				else:
					temp = []
					for one_item in item_list:
						temp.append( json.dumps([one_item], allow_nan=True) )
					writer.writerow( temp )
		except Exception as ex:
			spider.logger.error( f"cannot write csv file in Method write_one_row of Class DianpingPipeline. Exception = {ex}; item_list = {item_list}; all_keys = {all_keys}; item={item}" )

	def close_spider(self, spider):
		pass
		# will try to place disk I/O here by writing pandas df to csv file
