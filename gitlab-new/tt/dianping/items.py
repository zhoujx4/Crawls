# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Item, Field

class DianpingItem(scrapy.Item):
	# define the fields for your item here like:
	shop_id = Field()
	name = Field()
	comment = Field()
	scores = Field()
	statistics = Field()
	targeted_page = Field()

	# Housekeeping fields
	url = Field()
	project = Field()
	spider = Field()
	server = Field()
	date = Field()

class DianpingListItem(scrapy.Item):
	# define the fields for your item here like:
	category_id = Field()
	category_list = Field()
	shop_list = Field()
	css_url = Field()
	targeted_page = Field()
	decoded_shop_dict = Field()

	# Housekeeping fields
	url = Field()
	project = Field()
	spider = Field()
	server = Field()
	date = Field()
