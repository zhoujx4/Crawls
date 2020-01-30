import os
import sys
import csv
import shutil

# ERROR: after 4 minutes, there are still 74 waiting for response: 
xy_on_water_list = [
	'113.497386,23.683558', '112.897416,23.503565', '112.897385,22.843559', '113.737385,22.603558', '113.737385,22.483558', '113.737415,22.663564', 
	'114.517363,22.423822', '113.797334,22.363815', '113.857385,22.483558', '113.797363,22.423821', '114.577415,22.663563', '113.857384,22.363558', 
	'113.797363,22.543821', '113.737385,22.723558', '114.517334,22.483816', '113.857414,22.303564', '113.737414,22.423564', '114.577385,22.603557', 
	'113.857414,22.423564', '113.797334,22.483815', '113.677333,23.083815', '114.157363,22.783822', '114.097415,22.903563', '113.977415,23.023564', 
	'113.677363,22.783821', '113.617415,22.903564', '114.037363,23.023822', '113.977385,22.843558', '114.097415,23.023563', '114.097385,22.843558', 
	'114.037333,23.083815', '113.677334,22.843815', '113.557363,23.023821', '113.737415,22.783564', '114.037333,22.963815', '113.677363,22.903821', 
	'113.617385,23.083558', '113.857385,22.963558', '113.737385,22.963558', '114.037334,22.843815', '113.797363,23.023821', '113.797363,22.783821', 
	'113.917333,23.083815', '114.217385,22.843558', '114.097415,22.783563', '113.917334,22.843815', '113.917363,22.903821', '114.217415,22.903563', 
	'113.617385,22.843558', '113.797334,22.963815', '113.917333,22.963815', '114.037363,22.783822', '113.977415,22.903564', '113.737415,22.903564', 
	'113.677334,22.963815', '114.217385,22.963558', '113.977385,23.083558', '113.797334,22.843815', '113.617415,23.023564', '114.157363,22.903822', 
	'114.037363,22.903822', '113.857385,23.083558', '113.737385,23.083558', '113.737415,23.023564', '113.977385,22.963558', '114.157334,22.723815', 
	'113.797363,22.903821', '113.737385,22.843558', '113.857415,22.903564', '113.557334,22.963815', '113.797333,23.083815', '114.157333,22.963815', 
	'113.857385,22.843558', '114.157334,22.843815'
]
on_waters = 22.723558 + 0.01
for index, row in enumerate( xy_on_water_list ):
	xy_list = row.split(",")
	y = float(xy_list[1])
	if y < on_waters:
		print( f"1,{row},0,0,14000" )
sys.exit(3)
# OBJECTID,x,y,ok0,max,max_timestamp
# 1,113.803874,23.80969,0,0,14000
# 1,113.383874,22.96969,0,0,14000
log_dir = os.getcwd()
file_name = "xy_with_zero.log"
log_file_path = os.path.join( log_dir, file_name )
try:
	with open( log_file_path, "w", encoding="utf-8" ) as xy_log_file:
		for index, row in enumerate( xy_on_water_list ):
			xy_log_file.write( f"1,{row},0,0,14000\n" )
except Exception as ex:
	print( f"cannot write historical xy_log_file ({log_file_path}). Exception = {ex}" )
sys.exit(3)

log_dir = os.getcwd()
xy_response_log_file_name = "test_seen_xy.log"
log_file_path = os.path.join( log_dir, xy_response_log_file_name )
bak_file_name = xy_response_log_file_name.replace(".log", ".bak")
bak_file_path = os.path.join( log_dir, bak_file_name )
shutil.copyfile( log_file_path, bak_file_path )
xy_seen_dict = {
	"113.737414,22.543564": 3,
	"113.737414,23.543564": 6,
	"113.737414,24.543564": 8,
}
try:
	with open( log_file_path, "w", encoding="utf-8" ) as xy_log_file:
		for index, center_xy_str in enumerate( xy_seen_dict ):
			item = xy_seen_dict[center_xy_str]
			xy_log_file.write( f"{center_xy_str},{item}\n" )
except Exception as ex:
	print( f"cannot write historical xy_log_file ({log_file_path}). Exception = {ex}" )
sys.exit(3)

string = ""
converted = int( string )
print( type(converted) )
print( converted )
sys.exit(3)

root_path = os.getcwd()
xy_file_name = "data4cities_amap.txt"
xy_file_path = os.path.join( root_path, xy_file_name )
new_xy_file_path = os.path.join( root_path, "data4cities_amap02.txt" )
try:
	with open( xy_file_path, "r", encoding="utf-8" ) as f:
		content_list = f.readlines()[1:]
		with open( new_xy_file_path, "a", encoding="utf-8", newline="") as new_file:
			writer = csv.writer( new_file )
			for one in content_list:
				xy_str = one.strip("\n")
				xy_list = xy_str.split(",")
				if 2 == len(xy_list):
					x = xy_list[0].strip('"')
					y = xy_list[1].strip('"')
					writer.writerow( [float(x), float( y )] )
except Exception as ex:
	print( f"cannot read xy_list file ({xy_file_path}). Exception = {ex}" )