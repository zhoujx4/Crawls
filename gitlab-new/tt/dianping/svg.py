# -*- coding: utf-8 -*-
import requests
from requests.exceptions import RequestException
import os
import sys
import time
import csv
import pandas as pd
import numpy as np
import re
import math

from tt.extensions.commonfunctions import CommonClass

class ExtractSVG(object):
	"""__init__ method accepts:
	root_path: string, the root path of the css file and svg files
	css_file: string, the file name of the css file
	css_file_path: string, the full path of this css file; shall be in svgtextcss folder
	css_string: string (NOT bytes!), if css_file is not provided, css_string is the content of this file
	send_requests: bool, whether request svg files using urls in css file if no svg files in root_path
	referer: string, last html request uri
	save_requested_svg: bool, whether to save the svg file after successful request
	csv_file: string, if csv_file is not None, write the anti-crawled result to File root_path/spidername/svgtextcss/csv_file or root_path/spidername/svgtextcss_fiddler/csv_file
	settings: object, scrapy spider settings object
	folder: string, == list_html or detail_html
	logger: scrapy logger

	attributes:
	all parameters above and:
	epilson = 0.0000001
	svg_files: dict, all svg file names parsed from the css file. has keys like pcq, oul, or others, and values like 2e429b51c0d6dbda8229f44bd237a090.svg
	svg_urls: dict, all svg urls parsed from the css file
	svg_file_dict: dict, has keys like pcq, oul, or others, and values like:
		'element': like 'span', 'b', 'd', and many other html5 element names
		'filename': like 2e429b51c0d6dbda8229f44bd237a090.svg
		'url': like //s3plus.meituan.net/v1/mss_0a06a471f9514fc79c981b5466f56b91/svgtextcss/2e429b51c0d6dbda8229f44bd237a090.svg
	svg_file_contents: dict, has keys like pcq, oul, or others, and values like:
		'content': dict, doc_list with y keys and text rows as values,
		'type': 1,2,3 (doc_type)
	payload: dict, all x and y pairs as values and keys like pcqacr, nihpfx, pzsbwn, and so on
	class_mapping: dict, like pcq0rg:股, krfx1o:1, pcqr73:魔, nihau4:低
	key_length: int, how many chars in one key. like krf (3-char), av (2-char)
	"""
	root_path = None
	css_file = ""
	css_file_path = ""
	css_string = ""
	send_requests = False
	referer = None
	save_requested_svg = True
	csv_file = ""
	settings = None
	folder = None
	logger = None
	spider_name = ""
	svg_css_folder_name = ""
	use_proxy = False
	proxies = ""

	epilson = 0.0000001
	svg_fingerprints = ["<?xml", "<!DOCTYPE svg", ]
	svg_request_schema = "http:"

	svg_files = {}
	svg_urls = {}
	svg_file_dict = {}
	svg_file_contents = {}
	payload = {}
	class_mapping = {}
	class_mapping_updated = False
	key_length = 0

	def __init__(self, root_path="", css_file="", css_string = "", send_requests=False, referer=None, save_requested_svg=True, csv_file=None, settings = None, folder="", logger=None):
		# read fiddler
		self.settings = None if settings is None else settings
		temp = self.settings.get( name = "RUN_PURPOSE", default=None )
		self.read_fiddler = False
		if "PARSE_FIDDLER" == temp:
			self.read_fiddler = True

		self.root_path = os.getcwd() if root_path is None or 1 > len( root_path) else root_path
		self.folder = "list_html" if folder is None or 1 > len( folder ) else folder
		self.spider_name = self.settings.get( "SPIDER_NAME" ) if self.settings is not None else ""
		self.svg_css_folder_name = self.settings.get( "SVG_TEXT_CSS" ) if self.settings is not None else ""
		if self.read_fiddler:
			self.svg_css_folder_name = f"{ self.svg_css_folder_name }_fiddler"

		self.css_file = "" if css_file is None or 1 > len( css_file) else css_file
		if self.css_file is not None and 0 < len( self.css_file ):
			self.css_file_path = os.path.join( self.root_path, self.spider_name, self.svg_css_folder_name, self.css_file )
		self.css_string = "" if css_string is None or 1 > len( css_string ) else css_string
		self.send_requests = False if send_requests is None else send_requests
		self.referer = None if referer is None or 1 > len( referer ) else referer
		self.save_requested_svg = True if save_requested_svg is None else save_requested_svg
		self.csv_file = "" if csv_file is None or 1 > len( csv_file ) else csv_file
		self.logger = None if logger is None else logger
		if self.logger is None:
			print( f"please pass the logger!" )
			sys.exit(2)
		self.use_proxy = True if self.settings.get( "HTTPPROXY_ENABLED" ) else False
		proxy_dict = CommonClass.get_proxies( proxy_dict = {} )
		self.proxies = proxy_dict['http']

		self.svg_files = {}
		self.svg_urls = {}
		self.svg_file_dict = {}
		self.svg_file_contents = {}
		self.payload = {}
		self.class_mapping = {}
		self.class_mapping_updated = False
		self.key_length = 0

	def run(self):
		doc = None
		if 0 < len( self.css_string ):
			doc = self.css_string
		else:
			try:
				with open( self.css_file_path, 'r', encoding='utf-8') as f:
					doc = f.read()
			except Exception as ex:
				self.logger.error( f"cannot open {self.css_file_path} and css_string is NOT passed in. Exception = {ex}" )
		if doc is not None:
			# read the css file and store in this all_dicts
			all_dicts = self.format_css( doc )

			if self.svg_files is None or 1 > len( self.svg_files ):
				for index, key in enumerate(all_dicts['svg_file_names']):
					self.svg_files[ key ] = all_dicts['svg_file_names'][key]['filename']

			if self.svg_urls is None or 1 > len( self.svg_urls ):
				for index, key in enumerate(all_dicts['svg_file_names']):
					self.svg_urls[ key ] = all_dicts['svg_file_names'][key]['url']

			if self.svg_file_dict is None or 1 > len( self.svg_file_dict ):
				self.svg_file_dict = all_dicts['svg_file_names']

			if self.payload is None or 1 > len( self.payload ):
				self.payload = all_dicts['xy_dict']

			if self.svg_files is not None and 0 < len( self.svg_files ) and (self.svg_file_contents is None or 1 > len(self.svg_file_contents)):
				self.read_svg_files()

			for index, key in enumerate( self.payload ):
				self.class_mapping[ key ] = self.decode_xy( key[:self.key_length], self.payload[key] )
			
			# debug_string = CommonClass.debug_get_first10_from_dict(dict4string = self.class_mapping, first = 10)
			# print( f"first 10 of self.class_mapping = {debug_string}" )

			self.save_class_mapping()
	
	def check_class_mapping_nan(self):
		data = {
			'key': list( self.class_mapping.keys() ),
			'char': list( self.class_mapping.values() ),
		}
		dianping = pd.DataFrame( data=data, columns =['key', 'char'] )
		dianping['count_nan'] = dianping['char'].apply(lambda x: 1 if x is None or 1 > len(x) else 0 )
		nan_number = dianping.sum(axis = 0, numeric_only = True)
		nan_number = int( nan_number )
		return nan_number, dianping.shape[0]

	def write_csv_file(self, csv_file_path="", write_rows=True):
		try:
			with open( csv_file_path, 'w', encoding='utf-8', newline="") as f:
				writer = csv.writer(f)
				writer.writerow(['key', 'char', ])
				if write_rows:
					for index, key in enumerate( self.class_mapping ):
						writer.writerow( [key, self.class_mapping[key],] )
				return True
		except Exception as ex:
			self.logger.error( f"cannot open file {csv_file_path}; Exception = {ex}" )
		return False

	def check_each_key(self, key="", char=""):
		if key not in self.class_mapping.keys() or self.class_mapping[ key ] is None or 1 > len( self.class_mapping[ key ] ):
			if char is not None and not isinstance( char, float ) and 0 < len( char ):
				self.class_mapping[ key ] = char
				self.class_mapping_updated = True

	def merge_two_df( self, csv_file_path = "", class_mapping_nan = "", csv_full_file_path="" ):
		result = False
		try:
			dianping = pd.read_csv( csv_file_path )
			nan_df = dianping[ dianping.char.isnull() ]
			if nan_df.shape[0] == class_mapping_nan:
				return True
		except Exception as ex:
			self.logger.error( f"Error happened while pd.read_csv {csv_file_path}; Exception = {ex}" )
			return False
		else:
			self.class_mapping_updated = False
			dianping.apply(lambda row: self.check_each_key(key =row['key'], char = row['char']), axis=1)
			if self.class_mapping_updated:
				result = self.write_csv_file( csv_file_path=csv_file_path, write_rows=True)
				class_mapping_nan, class_mapping_shape0 = self.check_class_mapping_nan()
				if 0 == class_mapping_nan and result:
					result = self.write_csv_file( csv_file_path=csv_full_file_path, write_rows=False )
			# print( f"inside merge_two_df. self.class_mapping_updated= {self.class_mapping_updated};  " )
			return True
		
	def save_class_mapping(self):
		"""
		csv_file_path = C:\\Entrobus\\projects\\crawl\\20190214scrapy\\tt\\dianping\\svgtextcss_fiddler\\d21b952fda06ad9439a0c92a13aa2c56.css
		"""
		# print( f"inside save_class_mapping. len of self.class_mapping = {len(self.class_mapping)}" )
		csv_file_path = os.path.join( self.root_path, self.spider_name, self.svg_css_folder_name, self.csv_file)
		csv_full_file_path = os.path.join( self.root_path, self.spider_name, self.svg_css_folder_name, f"full_{self.csv_file}" )
		if os.path.isfile( csv_file_path ):
			if os.path.isfile( csv_full_file_path ):
				return True
			class_mapping_nan, class_mapping_shape0 = self.check_class_mapping_nan()
			# print( f"inside save_class_mapping. class_mapping_nan = {class_mapping_nan}; type = {type(class_mapping_nan)}" )
			if 0 == class_mapping_nan:
				self.write_csv_file( csv_file_path=csv_full_file_path, write_rows=False )
				return self.write_csv_file( csv_file_path=csv_file_path, write_rows=True) # over the existing csv_file_path
			elif 0 < class_mapping_nan:
				self.merge_two_df( csv_file_path = csv_file_path, class_mapping_nan = class_mapping_nan, csv_full_file_path=csv_full_file_path )
		else:
			class_mapping_nan, class_mapping_shape0 = self.check_class_mapping_nan()
			if 0 == class_mapping_nan:
				self.write_csv_file( csv_file_path=csv_full_file_path, write_rows=False )
			return self.write_csv_file( csv_file_path=csv_file_path, write_rows=True)

	def request_svg(self, key = ""):
		doc = None
		if key is None or 1 > len(key):
			return doc
		if key not in self.svg_urls.keys():
			self.logger.error( f"unknown key. {key} is NOT in self.svg_urls.keys() ({self.svg_urls.keys()})" )
			return doc
		url = f"{self.svg_request_schema}{self.svg_urls[key]}"
		
		headers = self.settings.get( "DEFAULT_REQUEST_HEADERS" )
		headers["User-Agent"] = self.settings.get( 'USER_AGENT' )
		if self.referer is not None:
			headers["Referer"] = self.referer
		if self.use_proxy:
			response = requests.get( url, headers=headers, proxies = self.proxies ) # , cookies=cookie, params=params
		else:
			response = requests.get( url, headers=headers ) # , cookies=cookie, params=params
		if 200 == response.status_code:
			doc = response.text
			if self.check_requested_svg_doc( key, doc ):
				return doc
			else:
				self.logger.warning( f"[warning] abnormal response after requesting {url}. response.text = {doc}" )
				return None
		else:
			self.logger.warning( f"[warning] wrong status_code after requesting {url}. response.status_code = {response.status_code}" )
			return None
	
	def check_requested_svg_doc( self, key="", doc = None ):
		if key is None or 1 > len( key ) or doc is None or 1 > len(doc):
			return False
		
		for one in self.svg_fingerprints:
			if -1 == doc.find( one ):
				return False

		if self.save_requested_svg and self.send_requests:
			if key not in self.svg_files.keys():
				self.logger.error( f"[error] unknown key. {key} is NOT in self.svg_files.keys() ({self.svg_files.keys()})" )
				return False
			svg_file = os.path.join( self.root_path, self.spider_name, self.svg_css_folder_name, self.svg_files[key])
			try:
				with open( svg_file, 'w', encoding='utf-8') as f:
					f.write( doc ) # overwrite existing file
			except Exception as ex:
				self.logger.warning( f"[warning] cannot write file {svg_file}; Exception = {ex}" )
				return True # even file is NOT written, still return True
		return True

	def read_svg_files( self ):
		svg_file_contents = {}
		doc = None
		for index, key in enumerate( self.svg_files ):
			svg_file = os.path.join( self.root_path, self.spider_name, self.svg_css_folder_name, self.svg_files[key])
			if not os.path.isfile( svg_file ) and self.send_requests:
				doc = self.request_svg(key)
				if doc is None:
					continue
			elif not os.path.isfile( svg_file ):
				continue
			
			if doc is None:
				try:
					with open( svg_file, 'r', encoding='utf-8') as f:
						doc = f.read()
				except Exception as ex:
					self.logger.error( f"Error! cannot open file {svg_file}; Exception = {ex}" )
					return False
			doc_type = self.check_svg_type( doc )
			if 1 == doc_type:
				doc_list = self.read_svg_path_doc( doc )
			elif 2 == doc_type:
				doc_list = self.read_svg_text_doc( doc )
			elif 3 == doc_type:
				doc_list = self.read_svg_number_doc( doc )
			else:
				self.logger.error( f"unknown svg file type, doc = {doc}; doc_type = {doc_type}" )
				continue
			temp_dict = {
				'content': doc_list,
				'type': doc_type,
			}
			svg_file_contents[ key ] = temp_dict
			doc = None
		
		# request could be longer than 10 seconds
		downloaded = False
		# for i in range(60):
		# 	time.sleep(1)
		# 	if len( svg_file_contents) == len( self.svg_files ):
		# 		self.svg_file_contents = svg_file_contents
		# 		downloaded = True
		# 		break

		# even not all files are downloaded, we still go ahead and do the decoding
		if not downloaded:
			self.svg_file_contents = svg_file_contents
		return True

	def read_svg_path_doc(self, doc=""):
		return_list = []

		# search all paths
		text = doc
		path_pattern = r'<path(\s)id=(\")(\d)+(\"\s)d=(\")M0(\s)(\d)+(\s)'
		searchObj = re.search( path_pattern, text, re.M|re.I )
		pointer = 0
		paths = []
		while( searchObj is not None ):
			search_tuple = searchObj.span()
			if 2 != len( search_tuple ):
				self.logger.error( f"Error: len of searchObj is NOT 2. searchObj = {searchObj}" )
				break
			pointer = searchObj.span()[1]
			if pointer > len(text) - 1:
				break
			text = text[pointer:]
			searched = searchObj.group()

			path_id = searched.replace( "<path id=\"", "" )
			end_pos = path_id.find("\"")
			if -1 == end_pos:
				self.logger.error( f"Error: cannot find ending \" of path_id ({path_id})" )
				break
			path_id = path_id[:end_pos]

			value_start_pos = searched.find("d=\"M0 ")
			if -1 == value_start_pos:
				self.logger.error( f"Error: cannot find start pos of searched ({searched})" )
				break
			value = searched[value_start_pos+6:]

			path_dict = {
				'id': int(path_id),
				'y': int(value),
			}
			paths.append( path_dict )
			searchObj = re.search( path_pattern, text, re.M|re.I )

		# <textPath xlink:href="#1" textLength="384">细酒原职既派凡云像恶首够遍交料归林卖完外莫项十工适甚架站野悲祖至</textPath>

		text_path_pattern = r'<textPath(\s)xlink:href=(\")#(\d)+'
		text_path_start_pattern = r'textLength=(\")(\d)+(\")>'
		searchObj = re.search( text_path_pattern, text, re.M|re.I )
		pointer = 0
		text_paths = {}
		while( searchObj is not None ):
			search_tuple = searchObj.span()
			if 2 != len( search_tuple ):
				self.logger.error( f"Error: len of searchObj is NOT 2. searchObj = {searchObj}" )
				break
			pointer = searchObj.span()[1]
			if pointer > len(text) - 1:
				break
			text = text[pointer:]
			searched = searchObj.group()
			path_id_pos = searched.find("\"")
			if -1 == path_id_pos:
				self.logger.error( f"Error: cannot find path_id. searched = {searched}" )
				break
			path_id = searched[path_id_pos+2:]
			
			# get the beginning pos
			search_text_obj = re.search( text_path_start_pattern, text, re.M|re.I )
			if search_text_obj is None:
				self.logger.error( f"Error: cannot find textPath of id {path_id}. text = {text}" )
				break
			search_tuple = search_text_obj.span()
			if 2 != len( search_tuple ):
				self.logger.error( f"Error: len of search_text_obj is NOT 2. search_text_obj = {search_text_obj}" )
				break
			pointer = search_text_obj.span()[1]
			if pointer > len(text) - 1:
				self.logger.error( f"Error: pointer overflow. text = {text}" )
				break
			text = text[pointer:]
			starting_pos = pointer
			before = text

			# get the ending pos
			ending_pos = text.find("</textPath>")
			if -1 == ending_pos:
				self.logger.error( f"Error: cannot find ending of text. text = {text}" )
				break
			text_content = text[:ending_pos]
			pointer = ending_pos
			text = text[pointer:]

			text_paths[ int(path_id) ] = text_content
			searchObj = re.search( text_path_pattern, text, re.M|re.I )

		for index, value in enumerate(paths):
			path_id = value['id']
			temp_dict = {
				'y': value['y'],
				'text': text_paths[path_id],
			}
			return_list.append( temp_dict )
		return return_list

	def read_svg_number_doc( self, doc="" ):
		number_list = []
		text = doc

		x_pattern = r'<text(\s)x=(\")'
		y_pattern = r'<text(\s)x=(\")[\d\s]+(\"\s)y=(\")(\d)+(\")'
		x_search_obj = re.search( x_pattern, text, re.M|re.I )

		while( x_search_obj is not None ):
			# find x
			pos = x_search_obj.span()
			if 2 != len( pos ):
				self.logger.error( f"Error! len of x_search_obj.span() is NOT 2. pos = {pos} " )
				break
			temp = text[pos[1]:]
			x_ending = temp.find(" ")
			x = int( temp[:x_ending] )

			# find y
			y_search_obj = re.search( y_pattern, text, re.M|re.I )
			searched = y_search_obj.group()
			y_list = searched.split("y=")
			if 2 != len( y_list ):
				self.logger.error( f"Error! len of y_list is NOT 2. y_list = {y_list} " )
				break
			y = int( y_list[1].replace('"', "") )

			# get value
			pos = y_search_obj.span()
			if 2 != len( pos ):
				self.logger.error( f"Error! len of y_search_obj.span() is NOT 2. pos = {pos} " )
				break
			ending_pos = text.find("</text>")
			value = text[pos[1] + 1:ending_pos]
			text = text[ending_pos+7:]
			this_dict = {
				"x": x,
				"y": y,
				"text": value,
			}
			number_list.append( this_dict )
			x_search_obj = re.search( x_pattern, text, re.M|re.I )

		return number_list

	def read_svg_text_doc(self, doc=""):
		text_list = []
		text = doc
		path_pattern = r'<text(\s)x=(\")0(\"\s)y=(\")(\d)+(\")'
		searchObj = re.search( path_pattern, text, re.M|re.I )
		pointer = 0
		while( searchObj is not None ):
			search_tuple = searchObj.span()
			if 2 != len( search_tuple ):
				self.logger.error( f"Error: len of searchObj is NOT 2. searchObj = {searchObj}" )
				break
			pointer = searchObj.span()[1] + 1
			if pointer > len(text) - 1:
				break
			text = text[pointer:]
			searched = searchObj.group()
			y_list = searched.split("y=")
			if 2 != len( y_list ):
				self.logger.error( f"Error: cannot find y=ddd. searched = {searched}" )
				break
			y = int( y_list[1].replace('"', '') )
			ending_pos = text.find("</text>")
			if -1 == ending_pos:
				self.logger.error( f"Error: cannot find ending label </text>. text = {text}" )
				break
			text_line = text[:ending_pos]
			pointer = 0
			text = text[ending_pos+7:]
			this_dict = {
				'y': y,
				'text': text_line,
			}
			text_list.append(this_dict)
			searchObj = re.search( path_pattern, text, re.M|re.I )
		return text_list

	# return 1 for svg containing path: font_height = 12
	# 2 for svg files containing only <text x="xx" y="xx">xxx</text>: font_height = 14
	def check_svg_type( self, doc = "" ):
		if doc is None or 1 > len( doc ):
			return 0
		if -1 < doc.find("<path"):
			return 1
		elif -1 < doc.find( "<text x=\"0\"" ):
			return 2
		elif -1 < doc.find("<text"):
			return 3
		return 0

	def get_char(self, string = "", index=0):
		char_list = list(string)
		if 1 > len( char_list ) or index > len(char_list) - 1:
			return ""
		return char_list[ index ]

	def calculate_pos( self, content={}, font_height=14, x=0, y=0 ):
		text = ""
		for one_line in content:
			if y < one_line["y"]:
				text = one_line["text"]
				break
		if 1 > len( text ):
			return ""
		if 0 == font_height:
			self.logger.error( f"Wrong font_height == 0 in self.svg_file_contents" )
			return ""
		index = math.floor( abs(x)/font_height )
		return self.get_char(string=text, index=index)

	# parameter first3 could be 2-char, 3-char, or other numbers of chars
	def decode_xy( self, first3= "", xy_dict={} ):
		if first3 is None or 1 > len( first3 ) or xy_dict is None or 1 > len( xy_dict ):
			return ""
		if first3 not in self.svg_file_contents.keys():
			return ""
		x = abs(xy_dict["x"])
		y = abs(xy_dict["y"])
		font_height = 0
		if 1 == self.svg_file_contents[first3]['type']:
			font_height = 12
			return self.calculate_pos( self.svg_file_contents[first3]['content'], font_height, x, y )
		elif 2 == self.svg_file_contents[first3]['type']:
			font_height = 14
			return self.calculate_pos( self.svg_file_contents[first3]['content'], font_height, x, y )
		elif 3 == self.svg_file_contents[first3]['type']:
			for one_line in self.svg_file_contents[first3]['content']:
				if y < one_line["y"]:
					font_height = one_line["x"]
					text = one_line["text"]
					break
			if 0 == font_height:
				self.logger.error( f"Wrong font_height in self.svg_file_contents[{first3}] = {self.svg_file_contents[first3]}" )
				return ""
			index = math.floor( abs(x)/font_height )
			return self.get_char(string=text, index=index)
		else:
			self.logger.error( f"Wrong self.svg_file_contents[{first3}] = {self.svg_file_contents[first3]}" )
			return ""

	def format_css(self, css=""):
		return_dict = {}
		if css is None or 1 > len(css):
			return return_dict
		csslen = len(css)
		i = 0
		xy_dict = {}
		svg_file_names = {}
		start = 0
		skip_font_face = False
		while i < csslen:
			if css[i] == '{':
				key = css[start:i]
				if -1 < key.find("."):
					key = CommonClass.clean_string( string = key, char_to_remove = ['\r', '\n', '\t', '.', ' ',] )
				elif -1 < key.find("class^="):
					key = CommonClass.clean_string( string = key, char_to_remove = ['\r', '\n', '\t', '.', ' ', ']', '"',] )
					key_list = key.split("[class^=")
					if 2 == len(key_list):
						key = f"{key_list[0]}___{key_list[1]}"
					else:
						self.logger.error( f"Error! key_list = {key_list}; key = {key}" )
						break
				elif -1 < key.find( "@font-face" ):
					skip_font_face = True
				else:
					self.logger.error( f"Error! key = {key}" )
					break
				value = None
				i += 1
				start = i
			elif css[i] == '}':
				value = css[start:i]
				value = CommonClass.clean_string( string = value, char_to_remove = ['\r', '\n', '\t', ] )

				if key is None or 1 > len(key):
					self.logger.error( f"Error! key is None. value = {value}" )
					break
				if -1 < value.find( "background:" ):
					value_list = value.split(" ")
					value_list = CommonClass.remove_0_len_element( list4remove = value_list )
					if 2 == len( value_list ):
						x_str = CommonClass.clean_string( string = value_list[0], char_to_remove = ['background:', 'px', ] )
						y_str = CommonClass.clean_string( string = value_list[1], char_to_remove = ['px;', ] )
						x = float(x_str)
						y = float(y_str)
						# x, y could equal to 0.0
						xy_dict[ key ] = { 'x':x, 'y':y, }
						key = None
					else:
						self.logger.error( f"Wrong value_list len. value = {value}; value_list = {value_list}" )
						break
				elif -1 < value.find( "background-image:" ):
					searchObj = re.search( r'url\((.*?)\)', value, re.M )
					if searchObj is None:
						self.logger.error( f"url not found. value = {value}" )
						break
					temp = searchObj.group()
					temp_list = temp.split("/")
					temp = CommonClass.clean_string( string = temp, char_to_remove = ["url(", ")"] )
					key_list = key.split("___")
					if 2 != len( key_list ):
						self.logger.error( f"Error! len of key_list is NOT 2. key_list = {key_list}; value = {value} " )
						break
					if key_list[1] in xy_dict.keys():
						self.logger.error( f"Error! xy_dict has key {key_list[1]}; value = {xy_dict[ key_list[1] ]}; value_list = {value_list}" )
						self.logger.info( xy_dict )
						break
					temp_dict = {
						'element': key_list[0],
						'filename': (temp_list[-1]).replace(')', ''),
						'url': temp,
					}
					svg_file_names[ key_list[1] ] = temp_dict
					if 1 > self.key_length:
						self.key_length = len(key_list[1])
					key = None
				elif skip_font_face:
					self.logger.warning( f"@font-face skipped" )
					skip_font_face = False
				else:
					self.logger.warning( f"background-image: not found. value = {value}; i = {i}" )
					# break # do NOT use break! just log it
				i += 1
				start = i
			else:
				i += 1
		return_dict['xy_dict'] = xy_dict
		return_dict['svg_file_names'] = svg_file_names
		return return_dict

if __name__ == "__main__":
	root_path = os.getcwd()
	root_path = os.path.join( root_path, "html_by_hand\\css_svg\\svg" )
	css_file = "1eb515893adcc915f7b5cb7d12b8772f_formatted.css"
	css_file = "1eb515893adcc915f7b5cb7d12b8772f.css"
	csv_file = "20190314.csv"
	referer = "http://www.dianping.com/shop/72457872"
	folder = "list_html"
	app = ExtractSVG(root_path = root_path, css_file = css_file, css_string = "", send_requests=True, referer=referer, save_requested_svg=True, csv_file = csv_file, settings = None, folder=folder )
	app.run()
