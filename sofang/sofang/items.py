# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SofangItem(scrapy.Item):
    '''
    title：标题
    city：城市
    house_name = 楼盘名称
    price：价格
    price_mean：均价
    hx：户型
    floor：户型
    area：面积
    decorating：装修
    chaoxiang：朝向
    year：楼盘年份
    address：所属区域
    longtidue：经度
    latitude：纬度
    url：网站
    date：日期
    '''
    title = scrapy.Field()
    city = scrapy.Field()
    price = scrapy.Field()
    price_mean = scrapy.Field()
    hx = scrapy.Field()
    floor = scrapy.Field()
    area = scrapy.Field()
    decorating = scrapy.Field()
    chaoxiang = scrapy.Field()
    year = scrapy.Field()
    house_name = scrapy.Field()
    address = scrapy.Field()
    longtidue = scrapy.Field()
    latitude = scrapy.Field()
    url = scrapy.Field()
    date = scrapy.Field()

