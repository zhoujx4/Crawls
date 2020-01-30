# coding=utf-8 

'''
Author: 周俊贤
Email：673760239@qq.com

date:2019/8/7 9:18
'''
import numpy as np
import pandas as pd
import json
import requests

def Get_Gaode_POI(item):
    item["longitude"] = np.nan
    item["latitude"] = np.nan
    item["adcode"] = np.nan


    base_gaode_url = "https://restapi.amap.com/v3/geocode/geo"
    headers = {
        'Accept': 'application/json,text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en,zh-cn.utf-8',
        # "Referer": "https://restapi.amap.com/v3/place/text",
    }


    two_requests_for_tryout = ['address', 'detail_address']
    for one_tryout in two_requests_for_tryout:
        result_dict = {}
        params = {
            "key": '4ebb849f151dddb3e9aab7abe6e344e2',
            "address": str(item[one_tryout]),
            "city": str(item['city']),
        }
        response = requests.get(base_gaode_url, headers=headers, params=params)
        if 200 == response.status_code:
            result_dict = parse_gaode_json(response.text)
        if 0 < (result_dict["count"]):
            item["longitude"] = result_dict["longitude"]
            item["latitude"] = result_dict["latitude"]
            item["adcode"] = result_dict["adcode"]
            break
    return item


def parse_gaode_json(json_text=""):
    return_dict = {
        "count": 0,
        "longitude": np.nan,
        "latitude": np.nan,
        "adcode": np.nan,
    }
    if 1 > len(json_text):
        return return_dict
    json_obj = json.loads(json_text)
    if json_obj is not None and "count" in json_obj.keys() and 0 < int(json_obj["count"]):
        if "geocodes" in json_obj.keys() and isinstance(json_obj["geocodes"], list) and 0 < len(json_obj['geocodes']):
            adcode = json_obj['geocodes'][0]['adcode']
            temp = json_obj['geocodes'][0]['location']
            temp_list = temp.split(',')
            if 1 < len(temp_list):
                longitude = temp_list[0]
                latitude = temp_list[1]
                return_dict['longitude'] = longitude
                return_dict['latitude'] = latitude
                return_dict['adcode'] = adcode
                return_dict["count"] = 1
    return return_dict

if __name__ == '__main__':
    pass