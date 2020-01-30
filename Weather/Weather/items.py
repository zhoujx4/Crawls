# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WeatherItem(scrapy.Item):
    # define the fields for your item here like:
    date = scrapy.Field()
    max  = scrapy.Field()
    min  = scrapy.Field()
    condition = scrapy.Field()
    city = scrapy.Field()

