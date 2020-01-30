# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Item, Field

class Gzzfcj1Item(scrapy.Item):
	# define the fields for your item here like:
	content = Field()
	page_type = Field()

	# Housekeeping fields
	url = Field()
	project = Field()
	spider = Field()
	server = Field()
	date = Field()
