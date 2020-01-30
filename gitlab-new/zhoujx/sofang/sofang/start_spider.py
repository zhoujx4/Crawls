# coding=utf-8 

'''
Author: 周俊贤
Email：673760239@qq.com

date:2019/8/6 23:08
'''
from scrapy import cmdline

cmdline.execute("scrapy crawl sofang_esfsale".split(" "))

# 下面爬虫目标源都需要爬取详情页面，每月更新1次：
# sofang_bsrent   搜房网租房-豪宅别墅频道：http://www.sofang.com/bsrent/area
# sofang_esfrent  搜房网租房-整租频道：http://gz.sofang.com/esfrent/area/aa1135-bl1
# sofang_esfsale  搜房网买房-二手房频道：http://www.sofang.com/esfsale/area/aa1135
# sofang_bssale   搜房网买房-豪宅别墅频道：http://www.sofang.com/bssale/area