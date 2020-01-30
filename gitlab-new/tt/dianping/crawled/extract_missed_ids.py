import re
import sys
import os
import re
import json
import numpy as np
import pandas as pd
import csv
import datetime
import math
import shutil

root_path = os.getcwd()
filename = "yueyang_hotel_shop_list.csv"
hotel = pd.read_csv( os.path.join( root_path, filename ) )
all_ids = []
for index, row in hotel.iterrows():
	all_ids.append( row['shop_id'] )

filename = "addresses.csv"
filepath = os.path.join( root_path, filename )
crawled_ids = []
if os.path.isfile( filepath ):
	crawled = pd.read_csv( filepath )
	for index, row in crawled.iterrows():
		crawled_ids.append( row['shop_id'] )

missed_ids = []
for shop_id in all_ids:
	if shop_id not in crawled_ids:
		missed_ids.append(shop_id)

txt_filename = "shop_id.txt"
with open( os.path.join( root_path, txt_filename ), 'a', encoding='utf-8', newline="") as f:
	writer = csv.writer(f)
	for shop_id in missed_ids:
		writer.writerow( [ shop_id ] )
print( f"{len(all_ids)} = {len(crawled_ids)} + {len(missed_ids)}" )

sys.exit(0)
