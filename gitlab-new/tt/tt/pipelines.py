# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import datetime

class TtPipeline(object):
	def process_item(self, item, spider):
		return item
	
	def close_spider(self, spider):
		pass
		# now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		# spider.logger.warning( f"Inside close_spider Method of Project's TtPipeline Class ({now})" )
