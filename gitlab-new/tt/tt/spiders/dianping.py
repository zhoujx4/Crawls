# -*- coding: utf-8 -*-
import datetime
import time
import socket
import os
import sys
import re
import json
import random
from urllib import parse
import numpy as np
import pandas as pd
import csv
import hashlib
import shutil

import scrapy
from scrapy.loader.processors import MapCompose, Join
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.http.response import Response
from scrapy.http import TextResponse
from scrapy.http.request import Request

from tt.extensions.commonfunctions import CommonClass
from dianping.items import DianpingItem
from dianping.items import DianpingListItem
from dianping.svg import ExtractSVG

class DianpingSpider(scrapy.Spider):
	"""
		sys.exit code == 1 # wrong or missing self.run_purpose
		sys.exit code == 2 # UnicodeDecodeError
		sys.exit code == 3 # Wrong file name
		On 20190517 Peter deleted 500-line codes that are no longer useful
	"""
	name = 'dianping'

	temp_str = ""				# temporary string used by Method replace_encoded()
	class_mapping_dict = {}		# temporary dict having structure like this:
	# {
	# 	'd21b952fda06ad9439a0c92a13aa2c56': {
	# 		'class_mapping': {'pufzt4':'屋', 'btk1j2': '成', and the like, },
	# 		'all_keys': ['puf', 'cmx', and the like, ],
	# 		'key_length': 3,
	# 	},
	# 	'711a35ed11322e6dc897d7918ffdaeb4': {
	# 		'class_mapping': {a key: char pair dict},
	# 		'all_keys': ['av', 'io', and the like, ],
	# 		'key_length': 2,
	# 	},
	# }

	# this attribute indicates the purpose of current run
	run_purpose = None
	root_path = None
	crawled_folder_name = None
	detail_html_folder_name = None
	list_html_folder_name = None
	svg_text_css_folder_name = None
	debug = False
	move_fiddler_file = True

	# while using proxy:
	proxy_meta = ""
	max_list_page = 50

	database_city_district_table = {}
	database_level2name_table = {}
	database_merchant_star_level_table = {}
	database_anticrawl20190505_table = {}
	database_common_channel_list_table = []

	custom_settings = CommonClass.get_custom_settings_dict(spider=name)

	def init_self_attributes(self):
		self.run_purpose = self.settings.get( name = 'RUN_PURPOSE', default=None )

		# set all paths
		self.root_path = self.settings.get( 'PROJECT_PATH' )
		self.crawled_folder_name = self.settings.get( name='CRAWLED_DIR', default='crawled' )
		self.detail_html_folder_name = self.settings.get( name='SAVED_DETAIL_HTML', default='detail_html' )
		self.list_html_folder_name = self.settings.get( name='SAVED_LIST_HTML', default='list_html' )
		self.svg_text_css_folder_name = self.settings.get( name='SVG_TEXT_CSS', default='svgtextcss' )
		if self.run_purpose in ["PARSE_FIDDLER", "PARSE_DETAILED_HOTEL", ]:
			self.detail_html_folder_name = f"{ self.detail_html_folder_name }_fiddler"
			self.list_html_folder_name = f"{ self.list_html_folder_name }_fiddler"
			self.svg_text_css_folder_name = f"{ self.svg_text_css_folder_name }_fiddler"

		# whether this run is for debugging
		self.debug = self.settings.get( name = 'PROJECT_DEBUG', default=False )
		self.move_fiddler_file = self.settings.get( name = 'MOVE_FIDDLER_HTML_FILE', default=True )

		# get proxy header
		temp = CommonClass.get_proxies( proxy_dict = {} )
		self.proxy_meta = temp['http']

		self.database_city_district_table = self.settings.get( name = 'DATABASE_CITY_DISTRICT_TABLE', default={} )
		self.database_level2name_table = self.settings.get( name = 'DATABASE_LEVEL2NAME_TABLE', default={} )
		self.database_merchant_star_level_table = self.settings.get( name = 'DATABASE_MERCHANT_STAR_LEVEL_TABLE', default={} )
		self.database_anticrawl20190505_table = self.settings.get( name = 'DATABASE_ANTICRAWL20190505_TABLE', default={} )
		self.database_common_channel_list_table = self.settings.get( name = 'DATABASE_COMMON_CHANNEL_LIST_TABLE', default=[] )

	def make_dirs(self):
		# even cache is used, we save all html files
		crawled_dir = os.path.join( self.root_path, self.name, self.crawled_folder_name )
		if not os.path.isdir( crawled_dir ):
			os.mkdir(crawled_dir)
		detail_html_dir = os.path.join( self.root_path, self.name, self.detail_html_folder_name )
		if not os.path.isdir( detail_html_dir ):
			os.mkdir(detail_html_dir)
		list_html_dir = os.path.join( self.root_path, self.name, self.list_html_folder_name )
		if not os.path.isdir( list_html_dir ):
			os.mkdir( list_html_dir )
		svg_css_dir = os.path.join( self.root_path, self.name, self.svg_text_css_folder_name )
		if not os.path.isdir( svg_css_dir ):
			os.mkdir( svg_css_dir )
		if self.run_purpose in ["PARSE_FIDDLER", "PARSE_DETAILED_HOTEL", ]:
			temp_foldername = self.detail_html_folder_name.replace( "_fiddler", "" )
			temp_dir = os.path.join( self.root_path, self.name, temp_foldername )
			if not os.path.isdir( temp_dir ):
				os.mkdir( temp_dir )
			temp_foldername = self.list_html_folder_name.replace( "_fiddler", "" )
			temp_dir = os.path.join( self.root_path, self.name, temp_foldername )
			if not os.path.isdir( temp_dir ):
				os.mkdir( temp_dir )
			temp_foldername = self.svg_text_css_folder_name.replace( "_fiddler", "" )
			temp_dir = os.path.join( self.root_path, self.name, temp_foldername )
			if not os.path.isdir( temp_dir ):
				os.mkdir( temp_dir )

	def start_requests(self):
		self.init_self_attributes()
		self.make_dirs()

		urls = [
			'http://quotes.toscrape.com/page/1/',
		]

		if self.debug:
			callback = self.parse_list_debug
		elif "PARSE_FIDDLER" == self.run_purpose:
			callback = self.parse_fiddler_list
			fiddler_list_dir = os.path.join( self.root_path, self.name, self.list_html_folder_name )
			file_list = os.listdir( fiddler_list_dir )
			for i in range( len( file_list ) ):
				urls.append( 'http://quotes.toscrape.com/page/1/' )
		elif "PARSE_DETAILED_HOTEL" == self.run_purpose:
			callback = self.parse_detailed_hotel_html
		else:
			self.logger.critical( f"self.run_purpose ({self.run_purpose}) can ONLY be PARSE_FIDDLER or PARSE_DETAILED_HOTEL" )
			sys.exit( 1 ) # wrong or missing self.run_purpose
		
		for url in urls:
			if self.run_purpose in ["PARSE_FIDDLER", "PARSE_DETAILED_HOTEL", ]:
				yield scrapy.Request( url=url, callback=callback, dont_filter=True )
			else:
				yield scrapy.Request( url=url, callback=callback )

	def parse_list_debug(self, response):
		pass
		# add whatever debug code here

	def parse_detailed_hotel_html(self, response):
		now = datetime.datetime.now()
		today = now.strftime( '%Y%m%d' )
		fiddler_detailed_dir = os.path.join( self.root_path, self.name, self.detail_html_folder_name )
		file_list = os.listdir( fiddler_detailed_dir )
		hotel_dict = {}
		file_path = ""
		for one_file in file_list:
			doc = None
			file_path = os.path.join( fiddler_detailed_dir, one_file )
			try:
				with open( file_path, 'r', encoding="utf-8", errors="ignore") as f:
					doc = f.read() # .decode(encoding='utf-8', errors='ignore')
			except Exception as ex:
				self.logger.critical( f"cannot read file {file_path}; Exception = {ex}" )
				sys.exit(2) # UnicodeDecodeError

			response = Selector( text=doc, type="html" )
			shop_id = one_file.strip( ".html" )
			shop_id = shop_id.strip( "shop" )
			hotel_address = response.xpath("//span[@class='hotel-address']/text()").extract_first(default="")
			if hotel_address is not None and 0 < len( hotel_address ):
				hotel_dict[shop_id] = hotel_address.strip("\"")
			else:
				self.logger.critical( f"cannot xpath hotel address from saved html file (shop_id = {shop_id})" )
				sys.exit(2)
		try:
			all_keys = ["shop_id", "hotel_address_newly_added", ]
			file_path = os.path.join( self.root_path, self.name, self.crawled_folder_name, f"addresses{today}.csv" )
			with open( file_path, 'a', encoding='utf-8', newline="") as f:
				writer = csv.writer(f)
				writer.writerow( all_keys )
				for index, shop_id in enumerate( hotel_dict ):
					writer.writerow( [ shop_id, hotel_dict[shop_id] ] )
		except Exception as ex:
			self.logger.error( f"cannot write csv file in Method parse_detailed_hotel_html of Class DianpingSpider. Exception = {ex}; file_path = {file_path}" )
		else:
			# move this html file
			if self.move_fiddler_file:
				for one_file in file_list:
					file_path = os.path.join( fiddler_detailed_dir, one_file )
					dst_path = file_path.replace("_fiddler", "")
					shutil.move(file_path, dst_path)

	def generate_filename_from_url(self, url="", file_type=""):
		response_html = ""
		filename = ""
		filename_base = ""
		folder = self.list_html_folder_name
		now = datetime.datetime.now()
		today = now.strftime( '%Y%m%d' )

		url_fragments = url.split("/")
		while '' in url_fragments:
			url_fragments.remove('')
		# Examples:
		# http://www.dianping.com/chenzhou/ch10/g113
		# http://www.dianping.com/shop/72457872
		# http://www.dianping.com/shop/8910906/review_all/p624
		if "list2" == file_type:
			if 3 < len( url_fragments ):
				filename_base = f"{url_fragments[-3]}_{url_fragments[-2]}_{url_fragments[-1]}"
				response_html = f"{filename_base}_{today}.html"
				filename = response_html
		elif "detailed" == file_type:
			folder = self.detail_html_folder_name
			if 3 < len( url_fragments ) and "review_all" == url_fragments[-2]:
				shop_id = CommonClass.find_digits_from_str( url_fragments[-3] )
				filename_base = f"shop_{shop_id}_{url_fragments[-1]}"
				response_html = f"{filename_base}_{today}.html"
				filename = response_html
			elif 2 < len( url_fragments ):
				shop_id = CommonClass.find_digits_from_str( url_fragments[-1] )
				filename_base = f"shop_{shop_id}_p1"
				response_html = f"{filename_base}_{today}.html"
				filename = response_html
		elif "css" == file_type:
			# http://s3plus.meituan.net/v1/mss_0a06a471f9514fc79c981b5466f56b91/svgtextcss/a59454e0c1813952099c1e006c298195.css
			folder = self.svg_text_css_folder_name
			if 1 < len( url_fragments ) and url_fragments[-1].endswith(".css"):
				filename_base = url_fragments[-1].replace(".css", "")
				response_html = url_fragments[-1]
				filename = response_html
		
		if response_html is None or 1 > len( response_html ):
			rand_int = random.randint(100000, 999999)
			response_html = f"unknown{rand_int}_{today}.html"
			self.logger.error( f"File {response_html} is used to store html page crawled from {url}" )

		return response_html, folder, filename, filename_base

	def save_crawled_page(self, response= None, file_type="list2"):
		# even cache is used, we save all html files
		response_html = ""
		url = ""
		
		if self.debug:
			if "list2" == file_type:
				url = "http://www.dianping.com/chenzhou/ch10/g113"
			else:
				url = "http://s3plus.meituan.net/v1/mss_0a06a471f9514fc79c981b5466f56b91/svgtextcss/a59454e0c1813952099c1e006c298195.css"
		elif hasattr(response, "url"):
			url = response.url
			
		response_html, folder, filename, filename_base = self.generate_filename_from_url(url=url, file_type=file_type)
		
		response_html = os.path.join( self.root_path, self.name, folder, response_html )
		try:
			with open( response_html, 'wb') as f:
				if hasattr(response, "body"):
					f.write(response.body)
				elif self.debug:
					f.write( response )
				return response_html
		except Exception as ex:
			self.logger.error( f"Fail to write file {response_html} for storing html page crawled from {url}; Exception = {ex}" )
			return ""

	def get_parse_dict_on_list_page(self, one_li=None, channel = "" ):
		"""the html pages in different channels have different xpath
			return the right dict according to the input channel
			self.database_common_channel_list_table includes all channels but 'hotel' and 'ch70'
		"""
		this_page_xpath = {}
		this_page_dict = {}
		need_clean = []
		use_extract = []
		need_split_and_clean = []
		if channel in self.database_common_channel_list_table:
			use_extract = ['group_deal_list']
			this_page_xpath = {
				'title': "./div[@class='txt']/div[@class='tit']/a/h4/text()" ,
				'shop_id': "./div[@class='txt']/div[@class='tit']/a/@data-shopid",
				'star': "./div[@class='txt']/div[@class='comment']/span[contains(@class, 'sml-rank-stars')]/@title",
				'group_deal': "./div/a[@data-click-name='shop_info_groupdeal_click']/@title",
				'group_deal_list': "./div[@class='svr-info']/div/a[@data-click-name='shop_info_groupdeal_click']/@title",
				# group_deal_list found in [ 'ch10', 'ch15', 'ch30', 'ch45', 'ch50', 'ch65', 'ch75', 'ch80', 'ch85', 'ch95', ]:

				'address': "./div/a[@data-click-name='shop_map_click']/@data-address",
				'out_of_business': "./div[@class='txt']/div[@class='tit']/span[@class='istopTrade']/text()",
			}
			if 'ch10' == channel:
				need_split_and_clean = ['recommended_dishes']
				this_page_xpath['takeway'] = "./div/a[@data-click-name='shop_info_takeway_click']/@title"
				this_page_xpath['recommended_dishes'] = "string(./div[@class='txt']/div[@class='recommend'])"
			elif channel in ['ch30', 'ch25']:
				this_page_xpath['group_deal'] = "./div[@class='txt']/div[@class='tit']/div/a[@class='igroup']/@title"
		elif channel in ['ch70', ]:
			this_page_xpath = {
				'title': "./div[@class='info baby-info']/p[@class='title']/a[@class='shopname']/text()",
				'branch': "./div[@class='info baby-info']/p[@class='title']/span[@class='icon-sale']/a[@class='shopbranch']/em/text()",
				'shop_id': "./@data-shopid",
				'star': "./div[@class='info baby-info']/p[@class='remark']/span[contains(@class, 'item-rank-rst')]/@title",
				'review_numbers': "./div[@class='info baby-info']/p[@class='baby-info-scraps']/span[@class='comment-count']/a/text()",
				'mean_prices': "string(./div[@class='info baby-info']/p[@class='baby-info-scraps']/span[@class='average'])",
				'group_deal': "./div[@class='info baby-info']/div[@class='tuan-info']/a[@class='tuan']/@title",
			}
			need_clean = ['mean_prices',]
		elif channel in ['ch90', ]:
			# ch90家装频道是201905以后增加的新频道，目前完全没有字符串加密。直接读取中文和数字即可
			this_page_xpath = {
				'title': "./div[@class='info baby-info']/p[@class='title']/a[@class='shopname']/text()",
				'branch': "./div[@class='info baby-info']/p[@class='title']/span[@class='icon-sale']/a[@class='shopbranch']/em/text()",
				'shop_id': "./@data-shopid",
				'star': "./div[@class='info baby-info']/p[@class='remark']/span[contains(@class, 'item-rank-rst')]/@title",
				'review_numbers': "./div[@class='info baby-info']/p[@class='baby-info-scraps']/span[@class='comment-count']/a/text()",
				'mean_prices': "string(./div[@class='info baby-info']/p[@class='baby-info-scraps']/span[@class='average'])",
				'group_deal': "./div[@class='info baby-info']/div[@class='tuan-info']/a[@class='tuan']/@title",
			}
			need_clean = ['mean_prices',]
		elif channel in ['hotel']:
			use_extract = ['hotel_tags']
			need_clean = ['place', 'price', ]
			this_page_xpath = {
				'shop_id': "./@data-poi",
				'title': "./div[@class='hotel-info-ctn']/div[@class='hotel-info-main']/h2[@class='hotel-name']/a/text()",
				'place': "string(./div[@class='hotel-info-ctn']/div[@class='hotel-info-main']/p[@class='place'])",
				'hotel_tags': "./div[@class='hotel-info-ctn']/div[@class='hotel-info-main']/p[@class='hotel-tags']/span/text()",
				'price': "string(./div[@class='hotel-info-ctn']/div[@class='hotel-remark']/div[@class='price']/p)",
				'star': "./div[@class='hotel-info-ctn']/div[@class='hotel-remark']/div[@class='remark']/div[@class='item-rank-ctn']/div[@class='item-rank-ctn']/span/@class",
				'review_numbers': "./div[@class='hotel-info-ctn']/div[@class='hotel-remark']/div[@class='remark']/div[@class='item-rank-ctn']/div[@class='item-rank-ctn']/a/text()",
			}

		if one_li is not None:
			for index, key in enumerate(this_page_xpath):
				if key in use_extract:
					temp_list = one_li.xpath( this_page_xpath[ key ] ).extract()
					this_page_dict[ key ] = CommonClass.get_cleaned_string_by_splitting_list(string_or_list = temp_list, char_to_remove = ['\r', '\n', '\t', ' ',])
				elif key in need_clean:
					temp_str = one_li.xpath( this_page_xpath[ key ] ).extract_first(default="")
					this_page_dict[ key ] = CommonClass.clean_string( string = temp_str, char_to_remove = ['\r', '\n', '\t', ' ',] )
				elif key in need_split_and_clean:
					temp_string = one_li.xpath( this_page_xpath[ key ] ).extract_first(default="")
					this_page_dict[ key ] = CommonClass.get_cleaned_string_by_splitting_list(string_or_list = temp_string, char_to_remove = ['\r', '\n', '\t', ' ',])
				else:
					this_page_dict[ key ] = one_li.xpath( this_page_xpath[ key ] ).extract_first(default="")
				
				# special fields
				if channel in ['hotel']:
					if 'star' in this_page_dict.keys():
						temp = this_page_dict['star'].replace("sml-rank-stars sml-str", "")
						if re.match( r'^(\d)+$', temp ):
							temp = int( temp )
							if temp in self.database_merchant_star_level_table.keys():
								this_page_dict['star'] = self.database_merchant_star_level_table[temp]
							else:
								this_page_dict['star'] = this_page_dict['star'].replace("sml-rank-stars sml-str", "")
						else:
							this_page_dict['star'] = temp
					if 'review_numbers' in this_page_dict.keys():
						this_page_dict['review_numbers'] = this_page_dict['review_numbers'].replace("(", "")
						this_page_dict['review_numbers'] = this_page_dict['review_numbers'].replace(")", "")
		shop_id = this_page_dict['shop_id'] if 'shop_id' in this_page_dict.keys() else '0'
		
		# extract special nodes
		# no by now
			
		return this_page_dict, shop_id

	def parse_shop_list(self, all_lis= [], css_svg_ready_for_decoding= True, constant_items = {}):
		shop_list = []
		decoded_shop_dict = {}
		city = constant_items['city']
		channel = constant_items['channel']
		this_level2 = constant_items['level2']
		this_level2_name = constant_items['level2name']
		for one_li in all_lis:
			this_page_dict, shop_id = self.get_parse_dict_on_list_page(one_li=one_li, channel = channel )
			this_page_dict.update( constant_items )
			if css_svg_ready_for_decoding:
				decoded_shop_dict[shop_id] = self.decode_fields( one_li=one_li, channel=channel )
			shop_list.append( this_page_dict )
		return shop_list, decoded_shop_dict

	def get_district_name( self, city = "", district = "" ):
		district_name = ""
		if 0 < len( city ) and city in self.database_city_district_table.keys():
			if district in self.database_city_district_table[ city ].keys():
				district_name = self.database_city_district_table[ city ][ district ]
		return district_name

	def parse_fiddler_list(self, response):
		"""for parsing html pages saved by fiddler
		"""
		fiddler_list_dir = os.path.join( self.root_path, self.name, self.list_html_folder_name )
		file_list = os.listdir( fiddler_list_dir )
		if 1 > len( file_list ):
			return None
		file_path = os.path.join( fiddler_list_dir, file_list[0] )
		doc = None
		try:
			with open( file_path, 'r', encoding="utf-8", errors='ignore') as f:
				doc = f.read() # .decode(encoding='utf-8', errors='ignore')
		except Exception as ex:
			self.logger.critical( f"cannot read file {file_path}; Exception = {ex}" )
			sys.exit(2) # UnicodeDecodeError

		response = Selector( text=doc, type="html" )

		# get all level2 categories
		filename_fragment_list = file_list[0].split("_")
		if 3 > len( filename_fragment_list ):
			self.logger.critical( f"file {file_list[0]} has wrong name" )
			sys.exit(3) # Wrong file name
		city = filename_fragment_list[0]
		channel = filename_fragment_list[1]
		this_level2, district = self.clean_this_level2_string( this_level2= filename_fragment_list[2] )
		district_name = ""
		if 0 < len( district ):
			district_name = self.get_district_name( city = city, district = district )
		categories, this_level2_name = self.get_categories_and_level2_name(response=response, city = city, channel = channel,  this_level2=this_level2)
		if 0 < len( district_name ):
			this_level2_name = this_level2_name + "_" + district_name
		if 1 > len( categories ): # this page has no categories
			city = filename_fragment_list[0]
			channel = filename_fragment_list[1]
		url = f"http://www.dianping.com/{city}/{channel}/{filename_fragment_list[2]}"

		# get the css request address
		css_url = None
		all_link_hrefs = response.xpath("//link[@rel='stylesheet']/@href").extract()
		for one_href in all_link_hrefs:
			if -1 < one_href.find("//s3plus.meituan.net"):
				css_url = one_href
		css_filename = ""
		if css_url is None:
			# when html file has no //s3plus.meituan.net/v1/mss_0a06a471f9514fc79c981b5466f56b91/svgtextcss/xxxx.css file, 
			# we try to use the latest css file downloaded
			this_svg_css_dir = os.path.join( self.root_path, self.name, self.svg_text_css_folder_name )
			css_filename = CommonClass.get_latest_file_name(this_dir = this_svg_css_dir, suffix=".css", logger = self.logger)
			css_url = f"//s3plus.meituan.net/v1/mss_0a06a471f9514fc79c981b5466f56b91/svgtextcss/{css_filename}"

		if 1 > len(css_filename):
			url_fragments = css_url.split("/") 
			if 1 < len( url_fragments ) and url_fragments[-1].endswith(".css"):
				css_filename = url_fragments[-1]
		csv_file = f"{css_filename}"
		csv_file = csv_file.replace(".css", ".csv")
		self.check_extract_svg_loaded( css_filename = css_filename, referer=css_url, csv_file=csv_file, folder="list_html_fiddler" )
		if "PARSE_FIDDLER" == self.run_purpose:
			self.read_all_css_files_for_mapping(referer = css_url, csv_file=csv_file, folder="list_html_fiddler" )
		css_svg_ready_for_decoding = True
		
		response_for_items = TextResponse( url=url, status=200, body=bytes(doc, encoding="utf-8") )
		loader = ItemLoader( item = DianpingListItem(), response = response_for_items )

		loader.add_value( 'category_id', f"{city}___{channel}" )
		loader.add_value( 'category_list', categories )
		loader.add_value( 'targeted_page', 'list2' )

		# get all shop_ids
		if channel in self.database_common_channel_list_table:
			all_lis = response.xpath("//div[@id='shop-all-list']/ul/li")
		elif channel in ['ch70']: # ch70 == 亲子
			all_lis = response.xpath("//ul[@class='shop-list']/li")
		elif channel in ['hotel']:
			all_lis = response.xpath("//ul[@class='hotelshop-list']/li[@class='hotel-block']")
		constant_items = {
			'city': city,
			'channel': channel,
			'level2': this_level2,
			'level2name': this_level2_name,
		}
		shop_list, decoded_shop_dict = self.parse_shop_list( all_lis= all_lis, css_svg_ready_for_decoding = css_svg_ready_for_decoding, constant_items=constant_items )
		
		loader.add_value( 'shop_list', shop_list )
		loader.add_value( 'css_url', css_url )
		loader.add_value( 'decoded_shop_dict', decoded_shop_dict )
		
		# record housekeeping fields
		loader.add_value('url', url)
		loader.add_value('project', self.settings.get('BOT_NAME') )
		loader.add_value('spider', self.name )
		loader.add_value('server', socket.gethostname() )
		loader.add_value('date', datetime.datetime.now().strftime("%Y%m%d_%H%M%S") )

		# move this html file
		if self.move_fiddler_file:
			dst_path = file_path.replace("_fiddler", "")
			shutil.move(file_path, dst_path)
		yield loader.load_item()

	def clean_this_level2_string(self, this_level2= ""):
		searchObj = re.search( r'p(\d)+$', this_level2 )
		if searchObj is not None:
			pos_tuple = searchObj.span()
			found_str = this_level2[pos_tuple[0]: pos_tuple[1]] # like p15
			this_level2 = this_level2.replace( f"{found_str}", "" )

		district = "" # 20190509 district code is added
		separators = ["r", "c", ]
		for separator in separators:
			if -1 < this_level2.find(separator):
				temp_list = this_level2.split(separator)
				if 1 < len( temp_list ):
					district = f"{separator}{temp_list[1]}"
				if 0 < len( temp_list ):
					this_level2 = temp_list[0]
				break
		return this_level2, district

	def get_categories_and_level2_name(self, response=None, city = "", channel = "", this_level2="" ):
		categories = []
		this_level2_name = ""
		if channel in self.database_common_channel_list_table:
			level2categories_a = response.xpath("//div[@id='classfy']/a")
			for one in level2categories_a:
				link = one.xpath("./@href").extract_first(default="")
				name = one.xpath("./span/text()").extract_first(default="")
				temp_dict = self.get_one_category( link = link, name = name )
				if temp_dict is not None and 0 < len( temp_dict ):
					categories.append( temp_dict )
					if this_level2 == temp_dict['level2']:
						this_level2_name = temp_dict['name']
		elif channel in ['ch70', ]:
			level2category_lis = response.xpath("//div[@id='nav']/div/ul/li[@class='first-item']")
			for one_li in level2category_lis:
				level2category_a = one_li.xpath( "./div[@class='primary-container']/span[@class='span-container']/a[@class='index-title' or @class='index-item']" )
				for one_a in level2category_a:
					link = one_a.xpath( "./@href" ).extract_first(default="")
					name = one_a.xpath( "string(.)" ).extract_first(default="")
					temp_dict = self.get_one_category( link = link, name = name )
					if temp_dict is not None and 0 < len( temp_dict ):
						categories.append( temp_dict )
						if this_level2 == temp_dict['level2']:
							this_level2_name = temp_dict['name']
		if 1 > len( this_level2_name ) and this_level2 in self.database_level2name_table.keys():
			this_level2_name = self.database_level2name_table[ this_level2 ]
		return categories, this_level2_name

	def get_one_category( self, link ="", name = ""):
		temp_dict = {}
		if name is not None and 0 < len( name ):
			temp_list = link.split("/")
			if 3 < len(temp_list):
				city = temp_list[-3]
				channel = temp_list[-2]
				level2 = temp_list[-1]
				temp_dict = {
					'name': name,
					'city': city,
					'channel': channel,
					'level2': level2,
					'link': link,
				}
		return temp_dict

	def decode_fields(self, one_li=None, channel = "" ):
		return_dict = {}
		if one_li is None:
			return return_dict
		if channel in self.database_common_channel_list_table:
			review_number_a = one_li.xpath("./div[@class='txt']/div[@class='comment']/a[@class='review-num']")
			review_numbers = self.get_decoded_str( element = review_number_a )
			mean_price_a = one_li.xpath("./div[@class='txt']/div[@class='comment']/a[@class='mean-price']")
			mean_prices = self.get_decoded_str( element = mean_price_a )

			# 总分/口味/质量/环境comment-list：[ 'ch10', 'ch15', 'ch20', 'ch50', 'ch75', 'ch85', 'ch95', ]
			comment_score_span = one_li.xpath("./div[@class='txt']/span[@class='comment-list']/span")
			comment_score_str = ""
			for one_span in comment_score_span:
				if 1 > len( comment_score_str ):
					comment_score_str = self.get_decoded_str( element = one_span )
				else:
					comment_score_str += f"; {self.get_decoded_str( element = one_span )}"
			
			return_dict = {
				'review_numbers': review_numbers,
				'mean_prices': mean_prices,
				'comment_score': comment_score_str,
			}
		elif channel in ['hotel0', 'ch70']:
			pass
			# there is no encoded fields in these 2 channels
		return return_dict

	def get_decoded_str(self, element = None ):
		if element is None:
			return ""
		self.temp_str = "" # need to initialize this!
		self.replace_encoded(element = element)
		return self.temp_str
		# <a class="review-num"><b>1<span class="niv48y"></span><span class="niv48y"></span><span class="niv8q4"></span></b>条点评</a>

	def replace_one_node_text(self, node = None, this_node_class_name20190505 = ""):
		if node is None:
			return ""
		this_node_class_name = node.xpath("./@class").extract_first(default="")

		# the following 7 lines are for updated anticrawl methods on 20190505
		this_node_get_text = node.get()
		if this_node_get_text is not None and 0 < len(this_node_get_text):
			this_node_get_text5 = this_node_get_text.encode('unicode_escape').decode('utf-8')
			if 6 == len( this_node_get_text5 ) and '\\' == this_node_get_text5[0] and 'u' == this_node_get_text5[1] and -1 < this_node_class_name20190505.find("shopNum"):
				key = this_node_get_text5[2:]
				if key in self.database_anticrawl20190505_table.keys():
					# self.logger.warning( f"{this_node_get_text5} ==> {key}; found in {self.database_anticrawl20190505_table[ key ]}" )
					return self.database_anticrawl20190505_table[ key ]
				# has no class as shopNum: ￥ ==> \uffe5
		
		not_in_class_mapping_dict = False

		for index,key in enumerate( self.class_mapping_dict ):
			this_dict = self.class_mapping_dict[key]
			key_length = this_dict['key_length']
			all_keys = this_dict['all_keys']
			if key_length < len(this_node_class_name) and this_node_class_name[ :key_length ] in all_keys:
				value = this_dict['class_mapping'][ this_node_class_name ] if this_node_class_name in this_dict['class_mapping'].keys() else ""
				if 0 < len( value ):
					return value
				else:
					not_in_class_mapping_dict = True
					self.logger.error(f"cannot find {this_node_class_name} in saved mapping class {key}.")
		if not_in_class_mapping_dict:
			return ""
		else:
			temp = CommonClass.clean_string( string = node.get(), char_to_remove = ['\r', '\n', '\t', ' ',] )
			return temp

	def replace_encoded(self, element = None):
		if element is None:
			return ""
		children = element.xpath("./child::node()")
		this_node_class_name20190505 = element.xpath("./@class").extract_first(default="")
		if 0 < len(children):
			for one_child in children:
				grandchild = one_child.xpath("./child::node()")
				if 0 < len( grandchild ):
					self.replace_encoded( element = one_child)
				else:
					this_node_text = self.replace_one_node_text( node = one_child, this_node_class_name20190505 = this_node_class_name20190505 )
					if this_node_text is not None and 0 < len( this_node_text ):
						self.temp_str += this_node_text
		else: # only node having no child needed to be decoded.
			this_node_text = self.replace_one_node_text( node = element, this_node_class_name20190505 = this_node_class_name20190505 )
			if this_node_text is not None and 0 < len( this_node_text ):
				self.temp_str += this_node_text

	def check_extract_svg_loaded(self, css_filename = "", css_string = "", referer = "", csv_file="", folder="" ):
		send_requests=True
		if "PARSE_FIDDLER" == self.run_purpose:
			send_requests=False
		app = ExtractSVG(root_path = self.root_path, css_file = css_filename, css_string = css_string, send_requests=send_requests, referer=referer, save_requested_svg=True, csv_file = csv_file, settings = self.settings, folder=folder, logger=self.logger )
		app.run()
		all_keys = app.svg_file_dict
		return_dict = {
			'class_mapping': app.class_mapping,
			'all_keys': all_keys.keys(),
			'key_length': int(app.key_length),
		}
		this_key = csv_file.replace(".csv", "")
		self.class_mapping_dict[this_key] = return_dict

	def read_all_css_files_for_mapping(self, referer = "", csv_file="", folder="" ):
		svg_css_dir = os.path.join( self.root_path, self.name, self.svg_text_css_folder_name )
		file_list = os.listdir( svg_css_dir )
		css_filename = csv_file.replace(".csv", ".css")
		for filename in file_list:
			if filename not in [css_filename] and filename.endswith(".css"):
				this_referer = referer.replace( css_filename, filename )
				csv_filename = filename.replace( ".css", ".csv" )
				self.check_extract_svg_loaded(css_filename = filename, css_string = "", referer = this_referer, csv_file=csv_filename, folder=folder )
