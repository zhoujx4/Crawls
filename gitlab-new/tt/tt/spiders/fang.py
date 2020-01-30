# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import Selector
import csv
import re
import sys
import os
import datetime
import random
import json
import numpy as np
import math
import socket

from scrapy.loader import ItemLoader
from scrapy.http import TextResponse

from tt.extensions.commonfunctions import CommonClass
from fang.items import FangItem

class FangSpider(scrapy.Spider):
	"""
		sys.exit code == 1 # wrong or missing RUN_PURPOSE
		sys.exit code == 2 # wrong or missing CRAWLED_DIR, SAVED_DETAIL_HTML, or SAVED_GAODE_JASON
		On 20190517 Peter re-write this spider for fixing bugs
	"""
	name = "fang"
	
	csv_filename = None
	root_path = ""
	run_purpose = None
	overwrite_today = ""
	crawled_dir = ""
	detail_html_dir = ""
	gaode_json_dir = ""
	csv_file_path = None
	custom_settings = CommonClass.get_custom_settings_dict(spider=name)
		
	def init_self_attributes(self):
		self.root_path = self.settings.get( "PROJECT_PATH" )
		self.run_purpose = self.settings.get( name = "RUN_PURPOSE", default=None )
		if self.run_purpose is None:
			self.logger.error( f"missing RUN_PURPOSE ({self.run_purpose}) setting" )
			sys.exit(1)
		self.overwrite_today = self.settings.get( "OVERWRITE_TODAY", default = "" )
		self.debug = self.settings.get( name = "PROJECT_DEBUG", default=False ) # whether this run is for debugging
		if not hasattr(self, "overwrite_today") or 1 > len( self.overwrite_today ) or self.overwrite_today is None:
			self.overwrite_today = datetime.datetime.now().strftime("%Y%m%d")

		# set all paths
		self.crawled_dir = self.settings.get( name='CRAWLED_DIR', default = "" )
		self.detail_html_dir = self.settings.get( name='SAVED_DETAIL_HTML', default="" )
		self.gaode_json_dir = self.settings.get( name='SAVED_GAODE_JASON', default="" )
		self.csv_file_path = os.path.join( self.crawled_dir, f"fang_zu{self.overwrite_today}.csv" )

		if 1 > len( self.crawled_dir ) or 1 > len( self.detail_html_dir ) or 1 > len( self.gaode_json_dir ):
			self.logger.info( f"missing CRAWLED_DIR ({self.crawled_dir}), SAVED_DETAIL_HTML ({self.detail_html_dir}), or SAVED_GAODE_JASON ({self.gaode_json_dir}) setting(s)" )
			sys.exit(2)

	def make_dirs(self):
		# even cache is used, we save all html files; here we make these 3 dirs if they do not exist
		if not os.path.isdir( self.crawled_dir ):
			os.makedirs( self.crawled_dir )
		if not os.path.isdir( self.detail_html_dir ):
			os.makedirs( self.detail_html_dir )
		if not os.path.isdir( self.gaode_json_dir ):
			os.makedirs( self.gaode_json_dir )

	def start_requests(self):
		self.init_self_attributes()
		self.make_dirs()

		if "READ_HTML" == self.run_purpose:
			url = 'http://quotes.toscrape.com/page/1/'
			yield scrapy.Request( url=url, callback=self.read_and_parse )
		elif "PRODUCTION_RUN" == self.run_purpose:
			city_list = self.settings.get( "CITY_LIST", default = [] )
			number_day_of_this_year = datetime.datetime.now().timetuple().tm_yday # type == int
			seperate_into_days = self.settings.get( "CRAWL_BATCHES", default = 3 )
			if seperate_into_days > len( city_list ):
				seperate_into_days = len( city_list )
			batch_count = math.ceil( len( city_list ) / seperate_into_days )
			today_batch = number_day_of_this_year % seperate_into_days
			start_index = today_batch * batch_count - 1
			end_index = ( today_batch + 1 ) * batch_count
			urls = []
			for index, city in enumerate(city_list):
				if (start_index < index) and (index < end_index):
					urls.append( f"https://{city}.zu.fang.com/" )
			for url in urls:
				yield scrapy.Request( url=url, callback=self.parse )
		else:
			urls = [
				'http://quotes.toscrape.com/page/1/',
				'http://quotes.toscrape.com/page/2/',
				'http://quotes.toscrape.com/page/3/',
				'http://quotes.toscrape.com/page/4/',
			]
			for url in urls:
				yield scrapy.Request( url=url, callback=self.do_nothing_for_debug )

	def do_nothing_for_debug(self, response):
		self.logger.info( f"inside Method do_nothing_for_debug of Class FangSpider. url = {response.url}" )

	def read_and_parse(self, response):
		file_list = os.listdir( self.detail_html_dir )
		for one_file in file_list:
			if -1 < one_file.find("index"):
				self.logger.info( f"ignoring {one_file}" )
			else:
				temp_list = one_file.split("_")
				apt_id = 0
				city_name = ""
				if 1 < len( temp_list ):
					apt_id = temp_list[1]
					city_name = temp_list[0]
				url = f"https://{city_name}.zu.fang.com/house/"
				html_file = os.path.join( self.detail_html_dir, one_file )
				if os.path.isfile(html_file):
					doc = None
					with open( html_file,'rb') as f:
						doc = f.read().decode('gb2312', 'ignore')
					if doc is None:
						self.logger.error( f"Error: cannot read html file {html_file}.")
						continue
					response = Selector( text=doc, type="html" )
					text = self.parse_response_field( response = response, city_name = city_name, apt_id = apt_id )
					try:
						response_for_items = TextResponse( url=url, status=200, body=bytes(doc, encoding="utf-8") )
						loader = ItemLoader( item = FangItem(), response = response_for_items )
						loader = self.load_items_into_loader( loader = loader, text = text, url = url )
						yield loader.load_item()
					except Exception as ex:
						print( f"Error happened during parsing in Method read_and_parse of Class FangSpider. Exception = {ex}" )
	
	def load_items_into_loader(self, loader = None, text = {}, url = ""):
		loader.add_value( 'content', str(text) ) # , encoding="utf-8"
		loader.add_value( 'page_type', "detailed" )

		# record housekeeping fields
		loader.add_value('url', url)
		loader.add_value('project', self.settings.get('BOT_NAME') )
		loader.add_value('spider', self.name )
		loader.add_value('server', socket.gethostname() )
		loader.add_value('date', datetime.datetime.now().strftime("%Y%m%d_%H%M%S") )
		return loader

	def parse_response_field(self, response = None, city_name = "", apt_id = ""):
		text = {}
		if response is None:
			return text
		if "READ_HTML" == self.run_purpose and not isinstance( response, Selector ):
			return text
		address_list = response.xpath('//div[@class="trl-item2 clearfix"]/div[@class="rcont"]')
		address = address_list[0].xpath('//div[@class="rcont"]/a/text()').extract_first(default="") if 0 < len( address_list ) else ""
		location_list = response.xpath('//div[@class="trl-item2 clearfix"]/div[@class="rcont address_zf"]/a/text()').extract()
		if location_list is None or 1 > len( location_list ):
			location_list = response.xpath('//div[@class="trl-item2 clearfix"]/div[@class="rcont"]/a[@class="link-under"]/text()').extract()
			address_list = response.xpath('//div[@class="trl-item2 clearfix"]/div[@class="rcont"]/a[not(@class)]/text()').extract()
			address = ""
			if 0 < len( address_list ):
				address = "；".join( address_list )
		location_list.reverse()
		location = ""
		for one_location in location_list:
			location += one_location
		if 0 < len( address ):
			address = CommonClass.clean_string( string = address, char_to_remove = ['\r', '\n', '\t', '"', ] )
		if 0 < len( location ):
			location = CommonClass.clean_string( string = location, char_to_remove = ['\r', '\n', '\t', '"', ] )
		rent_div = response.xpath('//div[@class="tr-line clearfix zf_new_title"]/div[@class="trl-item sty1 rel"]')
		if rent_div is None or 1 > len(rent_div):
			rent_div = response.xpath('//div[@class="tr-line clearfix zf_new_title"]/div[@class="trl-item sty1"]')
		temp = rent_div.css('::text').extract()
		rent_list = []
		for one_rent in temp:
			temp2 = one_rent.replace("\n", " ")
			temp2 = temp2.strip()
			if 0 < len( temp2 ):
				rent_list.append( temp2 )
		while "" in rent_list:
			rent_list.remove("")
		rent = ""
		if 1 < len( rent_list ):
			rent = rent_list[0] + rent_list[1]
		rent_type_div = response.xpath('//div[@class="trl-item1 w146"]/div[@class="tt"]')
		rent_type = rent_type_div[0].css('div::text').extract_first(default="") if 0 < len( rent_type_div ) else ""
		facing = rent_type_div[1].css('div::text').extract_first(default="") if 1 < len( rent_type_div ) else ""
		apt_type_div = response.xpath('//div[@class="trl-item1 w182"]/div[@class="tt"]')
		apt_type = apt_type_div[0].css('div::text').extract_first(default="") if 0 < len( apt_type_div ) else ""
		floor = apt_type_div[1].css('div::text').extract_first(default="") if 1 < len( apt_type_div ) else ""
		area_div = response.xpath('//div[@class="trl-item1 w132"]/div[@class="tt"]')
		area = area_div[0].css('div::text').extract_first(default="") if 0 < len( area_div ) else ""
		decorate = area_div[1].css('div::text').extract_first(default="") if 1 < len( area_div ) else ""
		update_date_spans = response.xpath('//p[@class="gray9 fybh-zf"]/span')
		update_date = ""
		if 1 < len( update_date_spans ):
			update_date = update_date_spans[1].css("::text").extract_first(default="")
		text = {
			"rent_id": f"{city_name}_{apt_id.strip()}_{self.overwrite_today}",
			"location": location.strip(),
			"address": address.strip(),
			"rent": rent.strip(),
			"rent_type": rent_type.strip(),
			"facing": facing.strip(),
			"apt_type": apt_type.strip(),
			"floor": floor.strip(),
			"area": area.strip(),
			"decorate": decorate.strip(),
			"update_date": update_date.strip(),
		}
		return text

	def parse_one_detail_page( self, response = None, apt_id = 0, city_name="" ):
		self.logger.info( f"inside Method parse_one_detail_page (todo...) of Class FangSpider. url = {response.url}; apt_id = {apt_id}; city_name = {city_name}" )

	def url_contains_error(self, result_obj_path = ""):
		if not isinstance(result_obj_path, str) or 1 > len( result_obj_path ):
			return False
		path_fragment_list = result_obj_path.split("/")
		if 1 > len( path_fragment_list ):
			return False

		# https://sz.esf.fang.com/staticsearchlist/Error/Error404?aspxerrorpath=/house-a013057/i330/i330
		for one in path_fragment_list:
			if -1 < one.find("Error") or -1 < one.find("Error404") or -1 < one.find("staticsearchlist"):
				self.logger.info( f"Error! Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, url = {result_obj_path}" )
				return True

		# http://search.fang.com/captcha-verify/redirect?h=https://wuxi.zu.fang.com/chuzu/3_166962621_1.htm
		for one in path_fragment_list:
			if -1 < one.find("captcha") or -1 < one.find("verify"):
				self.logger.info( f"Need captcha-verify! Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, url = {result_obj_path}" )
				return True

		return False

	def parse(self, response):
		url = response.url
		# detailed page:		https://gz.zu.fang.com/chuzu/3_238110671_1.htm?channel=3,8
		# list page (first):	https://gz.zu.fang.com/
		# list page (next):		https://gz.zu.fang.com/house/i32/
		result_obj = parse.urlparse( url )
		has_url_error = self.url_contains_error( result_obj_path = result_obj.path )
		if has_url_error:
			return False
		detail_page = False
		now = datetime.datetime.now()
		
		url_list = url.split("/")
		while "" in url_list:
			url_list.remove("")
		html_filename = "{}.html".format( now.strftime("%Y%m%d_%H%M%S") )
		today = f'{now.strftime("%Y%m%d")}'
		apt_id = ""
		city_name = ""
		if 0 < len(url_list):
			last_part = url_list[ len(url_list) - 1 ]
			temp_list = url_list[1].split(".") # empty "" element has been removed; "gz.zu.fang.com" == url_list[1] # not a strong code
			city_name = temp_list[0]
			if -1 < last_part.find( ".htm" ):
				detail_page = True
				temp = last_part.split( "_" )
				if 1 < len(temp):
					apt_id = f"{temp[1]}"
					html_filename = f"{city_name}_{apt_id}_{today}.html"
			elif -1 < last_part.find("fang.com"):
				html_filename = f"{city_name}_index1_{today}.html"
			else:
				page = last_part[2:]
				html_filename = f"{city_name}_index{page}_{today}.html"
		html_file_path = os.path.join( self.detail_html_dir, html_filename )
		with open( html_file_path, 'wb') as f:
			f.write( response.body )
		if detail_page:
			text = self.parse_response_field( response = response, city_name = city_name, apt_id = apt_id )
			try:
				loader = ItemLoader( item = FangItem(), response = response )
				loader = self.load_items_into_loader( loader = loader, text = text, url = url )
				yield loader.load_item()
			except Exception as ex:
				print( f"Error happened during parsing in Method read_and_parse of Class FangSpider. Exception = {ex}" )
		else:
			url_list = url.split("fang.com")
			base_url = ""
			if 0 < len(url_list):
				base_url = f"{url_list[0]}fang.com"
			total_pages = response.xpath('//div[@class="fanye"]/a/@href').extract()
			if 0 < len( total_pages ):
				last_page = total_pages[ len(total_pages) - 1 ] # /house/i33/
				last_page = last_page[9:]
				last_page = last_page.strip('/')
				if last_page is not None and 0 < len(last_page):
					for i in range( int(last_page) - 1 ):
						next_url = base_url + f'/house/i3{i + 2}/'
						self.logger.info( f"\ngoing to the next list page at {next_url}")
						yield response.follow(next_url, self.parse)
			apartments = response.xpath('//dl[@class="list hiddenMap rel"]/dt[@class="img rel floatl"]')
			for one_apt in apartments:
				next_url = base_url + one_apt.css("a::attr(href)").extract_first(default='')
				self.logger.info( f"\ngoing to the next detail page at {next_url}")
				yield response.follow(next_url, self.parse)
