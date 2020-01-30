# -*- coding: utf-8 -*-
import scrapy


class FangTestSpider(scrapy.Spider):
    name = 'fang_test'
    allowed_domains = ['fang.com']
    start_urls = ['https://yueyang.esf.fang.com/']

    def parse(self, response):
        yield scrapy.Request("https://yueyang.esf.fang.com/house-a012768/", callback=self.test, dont_filter=True)

    def test(self, response):
        print(response.text)