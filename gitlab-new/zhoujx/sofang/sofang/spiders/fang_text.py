# -*- coding: utf-8 -*-
import scrapy
import re
from sofang.items import SofangItem

class FangTextSpider(scrapy.Spider):
    name = 'fang_text'
    allowed_domains = ['sofang.com']
    start_urls = ['http://www.sofang.com/housedetail/sr2019050000031082.html/']
    # start_urls = ['http://api.ip.sb/ip']

    pattern = re.compile(r"[\r|\n|\s]*")

    def parse(self, response):
        print(response.text)
        pass
        # title = response.xpath("//p[@class='house_name']/text()").get()
        # price = response.xpath("//p[@class='total']//text()").getall()
        # price = " ".join(price)
        # price_mean = response.xpath("//p[@class='averages']/text()").get()
        # # hx = response.xpath("//div[@class='info']/dl[1]/dt/text()").getall()
        # # # hx = re.sub(FangTextSpider.pattern, "", hx)
        # # hx = FangTextSpider.pattern.sub('', hx)
        # area = response.xpath("//div[@class='info']/dl[2]/dt/text()").get()
        # decorating = response.xpath("//div[@class='info']/dl[2]/dd/text()").get()
        # chaoxiang = response.xpath("//div[@class='info']/dl[3]/dt/text()").get()
        # year = response.xpath("//div[@class='info']/dl[3]/dd/text()").get()
        # house_name = response.xpath("//ul[@class='msg']/li/a/text()").get()
        # address = response.xpath("//ul[@class='msg']/li[2]/span/text()").getall()
        #
        # coordinate = response.xpath("//li[@class='no_float'][2]/a/@href").get()
        # coordinate = re.search("longitude=(\d+.\d+)&latitude=(\d+.\d+)", coordinate)
        # longtidue = coordinate.group(1)
        # latitude = coordinate.group(2)
        #
        # print(items)
        # items = SofangItem(title=title, price=price, decorating=decorating, chaoxiang=chaoxiang,
        #               year=year, house_name=house_name, address=address, longtidue=longtidue, latitude=latitude)
        #
        # yield items
