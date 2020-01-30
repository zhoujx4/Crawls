# coding: utf-8
import requests
from requests.exceptions import RequestException
import json
import time
import datetime
import sys
import os
import csv
import random
import pandas
import math
import argparse
from operator import methodcaller
import configparser
import shutil

from easygo import transCoordinateSystem

class EasygoParser(object):
	xy_box = {}
	rootpath = ""
	data_tank_folder = ""
	log_folder = ""
	parse_log_folder = ""
	result_folder = ""

	def __init__(self, data_tank_folder = "", log_folder = "", result_folder = "", parse_log_folder = ""):
		self.rootpath = os.getcwd()
		self.data_tank_folder = data_tank_folder if 0 < len( data_tank_folder ) else "input"
		self.log_folder = log_folder if 0 < len( log_folder ) else "logs"
		self.parse_log_folder = parse_log_folder if 0 < len( parse_log_folder ) else "logs_parse"
		self.result_folder = result_folder if 0 < len( result_folder ) else "results"

	def save(self, text = "", time_now = "", file_name = "", remove_dirty = False, xy_box = {}):
		try:
			with open(file_name, 'r') as f:
				f.readline()
		except FileNotFoundError as ex:
			with open(file_name, 'w', encoding='utf-8') as f:
				f.write('count,wgs_lng,wgs_lat,time\n')
		
		# 写入数据
		with open(file_name, "a", encoding="utf-8") as f:
			if text is None:
				return
			node_list = json.loads(text)["data"]
			if node_list is None:
				self.write_log("请求结果为空")
			try:
				if json.loads(text).__contains__('max_data'):
					max_value = json.loads(text)['max_data']
				else:
					max_value=40
				min_count = max_value/40
				for i in node_list:
					# 此处的算法在宜出行网页后台的js可以找到，文件路径是http://c.easygo.qq.com/eg_toc/js/map-55f0ea7694.bundle.js
					#i['count'] = i['count']
					i['count'] = i['count'] / min_count
					gcj_lng = 1e-6 * (250.0 * i['grid_x'] + 125.0)
					gcj_lat = 1e-6 * (250.0 * i['grid_y'] + 125.0)
					#
					#lng, lat = transCoordinateSystem.gcj02_to_wgs84(gcj_lng, gcj_lat)
					#腾讯坐标系统转百度坐标
					lng, lat = transCoordinateSystem.gcj02_to_bd09(gcj_lng, gcj_lat)
					if remove_dirty:
						if lat > xy_box['min_lat'] and lat < xy_box['max_lat'] and lng > xy_box['min_lng'] and lng < xy_box['max_lng']:
							f.write( str(i['count']) + "," + str(lng) + "," + str(lat) + "," + time_now + "\n" )
					else:
						f.write( str(i['count']) + "," + str(lng) + "," + str(lat) + "," + time_now + "\n" )
			except IndexError as ex:
				self.write_log( f"IndexError happended in Method save. IndexError = {ex}" ) # f"此区域没有点信息"
			except TypeError as ex:
				self.write_log( f"TypeError happended in Method save. node_list = {node_list}; TypeError = {ex}" )

	def parse_crawled(self, city="yueyang_yueyanglouqu", subfolder = ""):
		"""
		subfolder == a string like: 20190520yueyang_yueyanglouqu_am
		"""
		today = datetime.datetime.now().strftime("%Y%m%d")
		jsons_path = os.path.join( self.rootpath, "jsons" ) # , subfolder
		# "20190416yueyanglouqu_am" "20190415yueyanglouqu_pm"
		# "20190515yueyang_am", "20190414yueyang_pm_all_area", 20190411shaoyang_pm_all,  20190411zhuzhou_am_all # "20190410zhuzhou_pm_cpp_ok"
		result_file_name = os.path.join( self.rootpath, self.result_folder, f"{city}_{today}.csv" )
		json_file_list = []
		for root, dirs, files in os.walk( jsons_path, topdown=False ):
			json_file_list = files
		for one_file in json_file_list:
			if one_file.endswith(".json"):
				xy_list = one_file.split("___")
				timestamp = xy_list[-1]
				timestamp = timestamp.strip(".json")
				time_now = time.strftime("%Y%m%d_%H%M%S", time.localtime( int(timestamp) ) )
				filepath = os.path.join( jsons_path, one_file )
				try:
					with open( filepath, 'r', encoding='utf-8' ) as f:
						doc = f.read()
						self.save( text = doc, time_now = time_now, file_name = result_file_name, remove_dirty = True, xy_box = self.xy_box )
				except Exception as ex:
					print( f"Exception happened while reading file {result_file_name} at {time_now}. Exception = {ex}" )

		# 20190520增加下面代码，将./jsons/*移动到./jsons_parsed/subfolder/*下面
		if 0 < len( subfolder ):
			target_dir = os.path.join( self.rootpath, "jsons_parsed", subfolder )
			if not os.path.exists( target_dir ):
				os.makedirs( target_dir )
			for one_file in json_file_list:
				file_path = os.path.join( jsons_path, one_file )
				dst_path = os.path.join( target_dir, one_file )
				shutil.move(file_path, dst_path)

	def write_log(self, content = None, logfilename = None, content_only = False):
		if content is not None and 0 < len( content ):
			today = datetime.datetime.now().strftime("%Y%m%d")
			if logfilename is None:
				logfilename = f"EasygoParser{today}.log"
			try:
				with open( os.path.join( self.rootpath, self.parse_log_folder, logfilename ),'a', encoding='utf-8' ) as f:
					if content_only:
						info = f"{str(content)}\n"
					else:
						info = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] {content}\n"
					f.write(info)
				return 1
			except Exception as ex:
				return 0
		return -1

	def get_xy_box(self, data_file_name = "yueyang2km_yueyanglouqu_with_zero.txt", add_delta= True, edge = 3.2 ):
		filepath = os.path.join( self.rootpath, self.data_tank_folder, data_file_name )
		center = []
		try:
			df = pandas.read_csv( filepath )
			for index, row in df.iterrows():
				center.append( "%.6f,%.5f" % (float(row['x']), float(row['y'])) )
		except Exception as ex:
			print( f"Exception happened while reading file. Exception = {ex}" )
			return None
		min_lng = 360
		max_lng = 0
		min_lat = 91
		max_lat = 0
		for one in center:
			xy_list = one.split(",")
			if 1 < len( xy_list ):
				try:
					x = float( xy_list[0] )
					y = float( xy_list[1] )
				except Exception as ex:
					print( f"ValueException. Exception = {ex}; xy_list = {xy_list}" )
				else:
					if x < min_lng:
						min_lng = x
					if x > max_lng:
						max_lng = x
					if y < min_lat:
						min_lat = y
					if y > max_lat:
						max_lat = y
		return_dict = {
			"min_lat": min_lat,
			"max_lat": max_lat,
			"min_lng": min_lng,
			"max_lng": max_lng,
		}
		if add_delta and 0 < edge:
			lng_delta = 0.01167 * edge
			lat_delta = 0.009009009 * edge
			return_dict["min_lat"] -= lat_delta
			return_dict["max_lat"] += lat_delta
			return_dict["min_lng"] -= lng_delta
			return_dict["max_lng"] += lng_delta
		return return_dict

	def remove_duplicate(self, filepath = ""):
		df = pandas.read_csv(filepath, sep=',')
		df.drop_duplicates(subset=['count','wgs_lng','wgs_lat'], keep='first', inplace=True)
		csv_name = filepath.replace(".csv", "_cleaned.csv")
		df.to_csv(csv_name,index=False)

	def run_parser(self, data_file_name="", city = "", subfolder = ""):
		app.xy_box = app.get_xy_box( data_file_name = data_file_name, add_delta= True, edge = 3.21 )
		app.parse_crawled(city = city, subfolder = subfolder)
		today = datetime.datetime.now().strftime("%Y%m%d")
		filepath = os.path.join( os.getcwd(), self.result_folder, f"{city}_{today}.csv" )
		app.remove_duplicate(filepath = filepath)

	def divide_one_city(self, data_file_name = "", areas_to_be_removed = []):
		filepath = os.path.join( self.rootpath, self.data_tank_folder, data_file_name )
		center = []
		try:
			with open( filepath, 'r', encoding='utf-8' ) as f:
				doc = f.read()
				temp = doc.split(";")
				for one in temp:
					center.append( one )
		except Exception as ex:
			print( f"Exception happened while reading {filepath}. Exception = {ex}" )
			return None
		print( len(center) )

		to_be_removed = []
		for one_area in areas_to_be_removed:
			filepath = os.path.join( self.rootpath, self.data_tank_folder, one_area )
			try:
				with open( filepath, 'r', encoding='utf-8' ) as f:
					doc = f.read()
					temp = doc.split(";")
					for one in temp:
						to_be_removed.append( one )
			except Exception as ex:
				print( f"Exception happened while reading {filepath}. Exception = {ex}" )
				return None
		print( len(to_be_removed) )
		return_list = []
		for one in center:
			if one not in to_be_removed and 0 < len( one ):
				return_list.append( one )
		print( len(return_list) )
		new_filename = data_file_name.replace(".txt", f"_{len(areas_to_be_removed)}excluded.txt")
		filepath = os.path.join( self.rootpath, self.data_tank_folder, new_filename )
		try:
			if not os.path.isfile( filepath ):
				new_file = True
			with open( filepath, 'a', encoding='utf-8', newline="") as f:
				writer = csv.writer(f)
				if new_file:
					writer.writerow( ['OBJECTID', 'x', 'y', 'ok0', 'max', 'max_timestamp' ] )
				for one in return_list:
					xy_list = one.split(",")
					if 2 == len( xy_list ):
						writer.writerow( ['1', xy_list[0], xy_list[1], "0", "0", "14000", ] )
		except Exception as ex:
			print( f"cannot create excluding file in Method divide_one_city of Class EasygoParser. Exception = {ex}" )

	def read_single_line_and_write_ok_zero(self, data_file_name = "", ok_zero_file = "", check0file = "", run_purpose = 1):
		"""
		if 1 == run_purpose: get_empty_server_returns; that means write the x, y values of all requests that returned 0 data for today's run
		if 2 == run_purpose: update the current input file with the new logs named ok_zero_file and check0file after today's run
		"""
		filepath = os.path.join( self.rootpath, self.data_tank_folder, data_file_name )
		checkfilepath = os.path.join( self.rootpath, self.log_folder, check0file )
		ok0filepath = os.path.join( self.rootpath, self.log_folder, ok_zero_file )
		center = []
		check_max = {}
		ok_zero = []
		old_zero_data = {}
		try:
			run_purpose = int(run_purpose)
			with open( filepath, 'r', encoding='utf-8' ) as f:
				df = pandas.read_csv( filepath )
				for index, row in df.iterrows():
					center.append( "%.6f,%.5f" % (float(row['x']), float(row['y'])) )
				if 2 == run_purpose:
					for index, row in df.iterrows():
						key = "%.6f___%.5f" % (float(row['x']), float(row['y']))
						temp_dict = {
							"x": "%.6f" % float(row['x']),
							"y": "%.5f" % float(row['y']),
							"timestamp": "%d" % int(row['max_timestamp']),
							"max_count": "%d" % int(row['max']),
							"ok0": "%d" % int(row['ok0']),
						}
						old_zero_data[key] = temp_dict
			with open( ok0filepath, 'r', encoding='utf-8' ) as f:
				for item in f.readlines():
					row = eval( item )
					if 4 == len(row):
						value = f"{row[1]}___{row[2]}"
						ok_zero.append( value )
			with open( checkfilepath, 'r', encoding='utf-8' ) as f:
				for item in f.readlines():
					row = eval( item )
					if 4 == len(row):
						key = f"{row[0]}___{row[1]}"
						temp_dict = {
							"x": row[0],
							"y": row[1],
							"timestamp": row[2],
							"max_count": row[3],
						}
						check_max[key] = temp_dict
					else:
						print( f"cannot split this row: {row}" )
		except Exception as ex:
			print( f"Exception happened while reading file. Exception = {ex}" )
			return None

		today = datetime.datetime.now().strftime("%Y%m%d")
		temp = check0file.replace( "check0.log", "" )
		if 0 < len( temp ):
			today = temp[-8:]
		if 1 == run_purpose:
			new_filename = data_file_name.replace(".txt", f"_{today}_return_zero.txt")
		else:
			new_filename = data_file_name.replace(".txt", f"_{today}.txt")

		filepath = os.path.join( self.rootpath, self.result_folder, new_filename )
		new_file = False

		try:
			if not os.path.isfile( filepath ):
				new_file = True
			with open( filepath, 'a', encoding='utf-8', newline="") as f:
				writer = csv.writer(f)
				if new_file:
					writer.writerow( ['OBJECTID', 'x', 'y', 'ok0', 'max', 'max_timestamp' ] )
				for one in center:
					xy_list = one.split(",")
					if 2 == len( xy_list ):
						key = f"{xy_list[0]}___{xy_list[1]}"
						if key in check_max.keys():
							zero_bit = 1
							if 30 > int( check_max[key]["max_count"] ):
								zero_bit = 0
							if 1 == run_purpose:
								if 1 > zero_bit and 1 > int( check_max[key]["max_count"] ):
									writer.writerow( ['1', xy_list[0], xy_list[1], str(zero_bit), check_max[key]["max_count"], check_max[key]["timestamp"], ] )
							elif 2 == run_purpose:
								if int(old_zero_data[key]['max_count']) < int( check_max[key]["max_count"] ):
									old_zero_data[key]['max_count'] = check_max[key]["max_count"]
									old_zero_data[key]['timestamp'] = check_max[key]["timestamp"]
									old_zero_data[key]['ok0'] = zero_bit
							else:
								writer.writerow( ['1', xy_list[0], xy_list[1], str(zero_bit), check_max[key]["max_count"], check_max[key]["timestamp"], ] )
			
			# overwrite data_file_name
			if 2 == run_purpose and 0 < len(old_zero_data):
				filepath = os.path.join( self.rootpath, self.data_tank_folder, data_file_name )
				print( f"overwriting {filepath}" )
				with open( filepath, 'w', encoding='utf-8', newline="") as f:
					writer = csv.writer(f)
					writer.writerow( ['OBJECTID', 'x', 'y', 'ok0', 'max', 'max_timestamp' ] )
					for index,key in enumerate(old_zero_data):
						writer.writerow( ['1', old_zero_data[key]['x'], old_zero_data[key]['y'], old_zero_data[key]['ok0'], old_zero_data[key]["max_count"], old_zero_data[key]["timestamp"], ] )

		except Exception as ex:
			print( f"cannot create old format file in Method read_single_line_and_write_ok_zero of Class EasygoParser. Exception = {ex}" )

	def initial_ok_zero_file(self, data_file_name = "" ):
		filepath = os.path.join( self.rootpath, self.data_tank_folder, data_file_name )
		center = []
		try:
			with open( filepath, 'r', encoding='utf-8' ) as f:
				doc = f.read()
				temp = doc.split(";")
				for one in temp:
					center.append( one )
		except Exception as ex:
			print( f"Exception happened while reading file. Exception = {ex}" )
			return None
		new_filename = data_file_name.replace(".txt", "_with_zero.txt")
		filepath = os.path.join( self.rootpath, self.data_tank_folder, new_filename )
		new_file = False

		try:
			if not os.path.isfile( filepath ):
				new_file = True
			with open( filepath, 'a', encoding='utf-8', newline="") as f:
				writer = csv.writer(f)
				if new_file:
					writer.writerow( ['OBJECTID', 'x', 'y', 'ok0', 'max', 'max_timestamp' ] )
				for one in center:
					xy_list = one.split(",")
					if 2 == len( xy_list ):
						writer.writerow( ['1', xy_list[0], xy_list[1], "0", "0", "14000", ] )
		except Exception as ex:
			print( f"cannot create old format file in Method initial_ok_zero_file of Class EasygoParser. Exception = {ex}" )

	def check_and_run_arguments(self, method_name = "", argument_list = [] ):
		"""
		The method written for parsing command lines
		"""
		complicate_argument_list = []
		dir_list = dir(self)
		if method_name not in dir_list:
			print( f"EasygoParser only has these methods: {dir_list}" )
			return False
		if method_name in complicate_argument_list and -1 == argument_list[0].find( "filename=" ):
			print( f"Method {method_name} of EasygoParser needs complicate arguments and can ONLY read arguments from a file" )

		arguments_dict = {}
		if -1 < argument_list[0].find( "filename=" ):
			filename_list = argument_list[0].split("=")
			if 2 != len( filename_list ):
				print( f"use filename=xxxx to let this script understand the argument file name" )
				return False
			arguments_dict = self.read_argument_file( filename = filename_list[1], method_name = method_name )
			if 1 > len( arguments_dict ):
				print( f"Warning! There is no argument in file {filename_list[1]}" )
		else:
			for one in argument_list:
				if -1 == one.find( "=" ):
					print( f"argument {one} needs = to separate key and value" )
					return False
				temp_list = one.split("=")
				if 2 != len( temp_list ):
					print( f"argument {one} needs ONLY one = to separate key and value" )
					return False
				arguments_dict[ temp_list[0] ] = temp_list[1]
		methodcaller( method_name, **arguments_dict )(self)
		# https://blog.csdn.net/pythondafahao/article/details/79616294
		# https://blog.csdn.net/chenjinyu_tang/article/details/8136841
		# https://www.cnblogs.com/2bjiujiu/p/7289961.html
		# https://docs.python.org/3/library/operator.html
		# https://python3-cookbook.readthedocs.io/zh_CN/latest/c08/p20_call_method_on_object_by_string_name.html
		# https://blog.csdn.net/mrqingyu/article/details/84403924
		# https://stackoverflow.com/questions/3061/calling-a-function-of-a-module-by-using-its-name-a-string

	def read_argument_file( self, filename = "", method_name = "" ):
		arguments_dict = {}
		file_path = os.path.join( self.rootpath, self.data_tank_folder, filename )
		if not os.path.isfile( file_path ):
			return arguments_dict
		today = datetime.datetime.now().strftime("%Y%m%d")
		section_anme = f"{today}{method_name}"
		try:
			# https://blog.csdn.net/zhusongziye/article/details/80024530
			conf = configparser.ConfigParser()
			conf.read( file_path, encoding="utf-8" )
			sections = conf.sections()
			items = conf.items( section_anme )
			for one in items:
				if 2 == len( one ):
					temp_seq = one[1]
					if -1 < one[1].find( "[" ) or -1 < one[1].find( "{" ):
						temp_seq = eval( one[1] )
					arguments_dict[ one[0] ] = temp_seq
		except Exception as ex:
			print( f"Inside Method read_argument_file, configparser error = {ex}" )
			return {}
		else:
			pass
		finally:
			return arguments_dict

if __name__ == "__main__":
	"""
	This is a command line script for parsing the easygo data (in json format) crawled
	"""
	parser = argparse.ArgumentParser(description='Use the following:', allow_abbrev=True)
	parser.add_argument( '-method', metavar="m", nargs='?', type=str, default = "run_parser", help='the EasygoParser method you need to run' )
	parser.add_argument( '-arguments', metavar="a", nargs='*', default = [], help='the EasygoParser method needs all these string arguments; each is in a key=value pair; type one space between pairs' )
	args = parser.parse_args()
	# https://blog.csdn.net/weixin_35653315/article/details/72886718
	# https://docs.python.org/3/library/argparse.html
	
	app = EasygoParser()
	app.check_and_run_arguments( args.method, args.arguments )
	sys.exit(0)
	