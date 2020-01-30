import pandas as pd
import json
import numpy as np
import os
import sys
import datetime
import time
import copy
from urllib import parse
from collections import Counter
from collections import Iterable

from scrapy.selector import Selector

class CheckFangesf(object):
	"""
		there are problems while crawling guangzhou, we need a new class for checking these problems
		we do not embed this class into the scrapy fangesf spider so that we can run this checking process
		separately
	"""

	guangzhou_district_dict = {
		"a080": "增城",
		"a078": "番禺",
		"a084": "南沙",
		"a0639": "花都",
		"a076": "白云",
		"a074": "海珠",
		"a072": "越秀",
		"a071": "荔湾",
		"a073": "天河",
		"a079": "从化",
		"a075": "黄埔",
		"a015882": "广州周边",
	}

	main_log_label_dict = {
		"[fangesfpa] INFO: Inside Method parse_list_page of Class FangesfSpider, requesting": "start_list_request",
		"[fangesfpa] INFO: requesting https": "start_detailed_request",
		"[fangesfpa] INFO: requesting Gaode using community name": "start_amap_json_request",
		"[fangesfpa] INFO: requesting list page at": "start_list_page2and_more_request",
		"[fangesfpa] ERROR": "errors",
	}

	root_path = ""
	log_file_folder_name = "logs"

	list_page_family_count_dict = {} # for intermedial runs
	records_on_each_page_dict = {}
	list_page1_url_list = []
	unique_detail_page_url_list = []

	def __init__( self ):
		super(CheckFangesf, self).__init__()
		self.root_path = os.getcwd()

	def extract_url_from_one_row(self, one_row = "" ):
		if -1 < one_row.find("; meta_dict"):
			temp_list = one_row.split("; meta_dict")
			if 0 < len( temp_list ):
				one_row = temp_list[0]
		start = one_row.find("https://")
		if -1 < start:
			return (one_row[start:]).rstrip("/")
		return ""

	def remove_i3_from_url(self, url = ""):
		if -1 < url.find("i3"):
			return url[:(url.find("i3") - 1) ]
		return url

	def check_main_log_file(self, main_log_file_name = ""):
		log_file_path = os.path.join( self.root_path, main_log_file_name )
		main_log_info = {}
		list_page1 = 0
		list_page2_and_more = 0
		detailed_page_url_list = []
		list_page_url_list = []
		list_page1_url_list = []
		self.list_page_family_count_dict = {}
		try:
			with open( log_file_path, "r", encoding="utf-8") as log_file:
				# get all items in list_page1_url_list (all list #1 page)
				# like this: https://gz.esf.fang.com/house-a084-b014468/
				# but not: https://gz.esf.fang.com/house-a084-b014468/i32
				for one_row in log_file.readlines():
					if -1 < one_row.find( "[fangesfpa] INFO: Inside Method parse_list_page of Class FangesfSpider, requesting" ):
						list_page1_url_list.append( self.extract_url_from_one_row( one_row = one_row ) )
				if 0 < len( list_page1_url_list ):
					for one in list_page1_url_list:
						self.list_page_family_count_dict[ one ] = 0

				log_file.seek(0)
				for one_row in log_file.readlines():
					for index, one_label in enumerate( self.main_log_label_dict ):
						info_type = self.main_log_label_dict[one_label]
						if -1 < one_row.find( one_label ):
							if "start_list_request" == info_type:
								list_page1 += 1
								list_page_url_list.append( self.extract_url_from_one_row( one_row = one_row ) )
							
							if "start_detailed_request" == info_type and -1 == one_row.find(".htm"):
								info_type = "start_list_request"
								temp_list = one_row.split("/")
								if 0 < len( temp_list ) and -1 == temp_list[ len( temp_list ) - 1 ].find("i3"):
									self.write_log( f"Main log error! {one_row}" ) # no print out, that is correct.
								elif 0 < len( temp_list ):
									list_page2_and_more += 1
									page2_and_more_url = self.extract_url_from_one_row( one_row = one_row )
									its_page1_url = self.remove_i3_from_url( url = page2_and_more_url )
									# self.write_log( f"page2_and_more_url = {page2_and_more_url}; its_page1_url = {its_page1_url}" )
									if its_page1_url in list_page1_url_list:
										self.list_page_family_count_dict[ its_page1_url ] += 1
									else:
										self.write_log( f"Error! {its_page1_url} is NOT in self.list_page_family_count_dict.keys()" )
									list_page_url_list.append( page2_and_more_url )
							elif "start_detailed_request" == info_type:
								temp_list = one_row.split("/")
								if 0 < len( temp_list ):
									apt_id = temp_list[ len( temp_list ) - 1 ]
									apt_id = apt_id.split(".htm")
									detailed_page_url_list.append( apt_id[0] )
							main_log_info[ info_type ] = main_log_info[ info_type ] + 1 if info_type in main_log_info.keys() else 1
							if "errors" == info_type:
								pass
		except Exception as ex:
			self.write_log( f"fail to read file. Exception = {ex}" )
		else:
			self.list_page1_url_list = list_page1_url_list
			self.unique_detail_page_url_list = list( set(detailed_page_url_list) )
			return main_log_info

	def read_files_to_count_unique_number(self, file_name_list = []):
		overall_id_list = []
		record_counter_dict = {}
		for one_file_name in file_name_list:
			this_file_apt_id_list = []
			file_path = os.path.join( self.root_path, one_file_name )
			try:
				fang_df = pd.read_csv( file_path )
			except Exception as ex:
				self.write_log( f"fail to open {file_path}" )
			else:
				fang_df['apt_id'].apply(lambda x: this_file_apt_id_list.append( x ) )
				temp_dict = {
					"total_records": len( this_file_apt_id_list ),
					"unique_records": len( list( set(this_file_apt_id_list) ) ),
				}
				overall_id_list.extend(this_file_apt_id_list)
				record_counter_dict[ one_file_name ] = temp_dict
		unique_overall_apt_id_number = len( list( set(overall_id_list) ) )
		return unique_overall_apt_id_number, record_counter_dict

	def read_crawled_list_html_log(self, crawled_list_html_log = "" ):
		"""
			shall be called after check_main_log_file method
		"""
		file_path = os.path.join( self.root_path, crawled_list_html_log )
		error_counter = 0
		temp_list_url_list = copy.deepcopy(self.list_page1_url_list)
		temp_list1_family_count_dict = copy.deepcopy(self.list_page_family_count_dict)
		temp_key_list = list( temp_list1_family_count_dict.keys() )
		try:
			with open( file_path, "r", encoding="utf-8") as log_file:
				for one_list_url in log_file.readlines():
					one_list_url = one_list_url.rstrip( "/\n" )
					page2_or_more = (-1 < one_list_url.find("i3"))
					if one_list_url not in self.list_page1_url_list and not page2_or_more:
						self.write_log( f"Error: {one_list_url}" )
						error_counter += 1
					elif one_list_url in temp_list_url_list:
						temp_list_url_list.remove( one_list_url )
					else:
						its_page1_url = self.remove_i3_from_url( url = one_list_url )
						if its_page1_url in temp_key_list:
							temp_list1_family_count_dict[its_page1_url] -= 1
		except Exception as ex:
			self.write_log( f"fail to open {file_path}. Exception = {ex}" )
		else:
			self.write_log( f"total wrong list urls: {error_counter}" )
			self.write_log( f"left over list page without response == {temp_list_url_list}" )
			self.write_log( "There are still some Page2 or more list page have no response: " )
			self.write_log( temp_list1_family_count_dict )

	def extract_link_list( self, response = None ):
		link_list = response.xpath('//div[@class="shop_list shop_list_4"]/dl[@class="clearfix"]/dd/h4[@class="clearfix"]/a/@href').extract()
		if 1 > len( link_list ):
			error_msg = f"Fail to extract links"
			self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {cls.__name__}, {error_msg}" )
		return link_list

	def parse_and_check_crawled_list_html_pages( self, crawled_detailed_html_folder_name = "" ):
		"""
			shall be called after read_crawled_list_html_log method
		"""
		self.records_on_each_page_dict = {}
		for index, key in enumerate( self.list_page_family_count_dict ):
			if 0 < self.list_page_family_count_dict[key]:
				for i in range( self.list_page_family_count_dict[key] ):
					url = key.rstrip("/")
					url = f"{url}/i3{i+2}"
					self.records_on_each_page_dict[ url ] = 0
			else:
				self.records_on_each_page_dict[ key ] = 0

		list_html_dir = os.path.join( self.root_path, crawled_detailed_html_folder_name )
		file_list = os.listdir( list_html_dir )
		all_detailed_links = []
		for one_file in file_list:
			file_path = os.path.join( list_html_dir, one_file )
			try:
				with open( file_path, "rb") as f:
					doc = f.read().decode("gb2312", "ignore")
				if doc is None:
					self.write_log( f"Error: cannot read html file {file_path}.")
					continue
				response = Selector( text=doc, type="html" )
				link_list = self.extract_link_list( response = response )

				# this means link_list has newly_seen_records while all_detailed_links has NOT
				newly_seen_record_list = list(set(link_list).difference(set(all_detailed_links)))
				if 59 > len(newly_seen_record_list):
					self.write_log( f"This has less than 59 new records. file name = {one_file}; new record number / total record number = {len(newly_seen_record_list)}/{ len(link_list) }" )
					# the sum of all this newly_seen_record_list will NOT equal to unique_records below!
				else:
					self.write_log( f"This has 59 or more new records. file name = {one_file}; record number == { len(link_list) }" )

				all_detailed_links.extend( link_list )
				self.write_log( f"{one_file} : " )
				# most printout looks like this:
				# gz_a084_b014468_index13_20190626.html : 60
			except Exception as ex:
				error_msg = f"Exception = {ex}"
				self.write_log( f"Inside Method {sys._getframe().f_code.co_name} of Class {self.__class__.__name__}, {error_msg}" )
		self.write_log( f"total detailed html records == {len( all_detailed_links)}" )
		unique_records = len( list( set(all_detailed_links) ) )
		self.write_log( f"unique_records = {unique_records}" )

	def write_log(self, content_str = "", log_file_name_str = "", content_only_bool = False):
		if isinstance( content_str, Iterable) and 0 < len( content_str ):
			if not isinstance( log_file_name_str, Iterable) or 1 > len( log_file_name_str ):
				today = datetime.datetime.now().strftime("%Y%m%d")
				log_file_name_str = f"{self.__class__.__name__}{today}.log"
			try:
				with open( os.path.join( self.root_path, self.log_file_folder_name, log_file_name_str ), "a", encoding="utf-8") as log_file:
					if content_only_bool:
						info = f"{str(content_str)}\n"
					else:
						info = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] {content_str}\n"
					log_file.write(info)
				return 1
			except Exception as ex:
				print( f"fail to write log. content = {content_str}; Exception = {ex}" )
				return 0
		return -1

if __name__ == "__main__":
	app = CheckFangesf()
	main_log_file_name = "log_fangesfpa20190626nansha.log"
	main_log_info = app.check_main_log_file( main_log_file_name = main_log_file_name )
	app.write_log( main_log_info )
	app.write_log( app.list_page1_url_list )
	app.write_log( app.list_page_family_count_dict )
	app.write_log( len(app.unique_detail_page_url_list) )

	crawled_list_html_log = "crawled_list_html.log"
	crawled_detailed_html_log = "crawled_detailed_html.log"
	app.read_crawled_list_html_log( crawled_list_html_log = crawled_list_html_log )

	folder_name = "20190626html"
	app.parse_and_check_crawled_list_html_pages( crawled_detailed_html_folder_name = folder_name )

	# file_name_list = ["fang_esf20190621.csv", "fang_esf20190623.csv",]
	# file_name_list = ["fang_esf20190621shaoguan.csv", ]
	# unique_overall_apt_id_number, record_counter_dict = app.read_files_to_count_unique_number( file_name_list = file_name_list )
	# app.write_log( unique_overall_apt_id_number )
	# app.write_log( record_counter_dict )
