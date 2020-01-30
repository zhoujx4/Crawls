# coding=utf-8 

'''
Author: 周俊贤
Email：673760239@qq.com

date:2019/8/4 10:27
'''
import pandas as pd
import json

file = open(r"D:\JC-JUN\fang\fang\fang_xf.json", 'rb')
list = []
for line in file.readlines():
    dic = json.loads(line)
    list.append(dic)

data = pd.DataFrame(list)


#映射
mapping ={
    'city' : '城市',
    'Area_covered'  : '占地面积',
    'Building_Category' : '物业类别',
    'Built_up_area':'建筑面积',
    'Decoration_Status':'装修状况',
    'Developers':'开发商',
    'Floor_condition':'楼层状况',
    'Greening_rate':'绿化率',
    'Parking_space':'停车位',
    'Project_Features':'项目特色',
    'Property_Category':'物业类型',
    'Property_Charge_Description':'物业费描述',
    'Property_Company':'物业公司',
    'Property_fee':'物业费',
    'The_total_number_of_households':'总户数',
    'Total_number_of_buildings':'楼栋总数',
    'Volume_ratio':'容积率',
    'Years_of_Property_Rights':'财产年限',
    'address':'地址',
    'huxing':'主力户型',
    'kaipan':'近期开盘',
    'price':'均价',
    'title':'名称',
    'url':'网址',
    'Sales':'售卖情况'
}

data = data.rename(columns= mapping)
data = data.to_csv('新房数据.csv', index=False)


