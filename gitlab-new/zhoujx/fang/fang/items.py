# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class FangItem_xf(scrapy.Item):
    xiaoqu = scrapy.Field()
    date = scrapy.Field()
    city = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    huxing = scrapy.Field()
    address = scrapy.Field()
    kaipan = scrapy.Field()
    longdong = scrapy.Field()

    #基本情况
    Property_Category = scrapy.Field()
    Project_Features = scrapy.Field()
    Building_Category = scrapy.Field()
    Decoration_Status = scrapy.Field()
    Years_of_Property_Rights = scrapy.Field()
    Developers = scrapy.Field()

    # 小区规划
    Area_covered = scrapy.Field()
    Built_up_area = scrapy.Field()
    Volume_ratio = scrapy.Field()
    Greening_rate = scrapy.Field()
    Parking_space = scrapy.Field()
    Total_number_of_buildings = scrapy.Field()
    The_total_number_of_households = scrapy.Field()
    Property_Company = scrapy.Field()
    Property_fee = scrapy.Field()
    Property_Charge_Description = scrapy.Field()
    Floor_condition = scrapy.Field()
    longitude = scrapy.Field()
    latitude  = scrapy.Field()
    adcode = scrapy.Field()

    #每一栋的售卖情况
    Sales = scrapy.Field()


class FangItem_esf(scrapy.Item):
    date = scrapy.Field()
    city = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    price_per = scrapy.Field()
    address = scrapy.Field()
    xiaoqu = scrapy.Field()
    longitude = scrapy.Field()
    latitude  = scrapy.Field()
    adcode = scrapy.Field()

