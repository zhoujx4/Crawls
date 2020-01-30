# -*- coding: utf-8 -*-

# 搜房网租房-豪宅别墅频道：http://www.sofang.com/bsrent/area

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from sofang.items import SofangItem
import datetime
import re


class SofangBsrentSpider(CrawlSpider):
    date = datetime.datetime.now().strftime('%Y-%m-%d-%H')
    custom_settings = {
        'ITEM_PIPELINES' : {'sofang.pipelines.BsrentPipeline': 300,}
    }
    name = 'sofang_bsrent'
    allowed_domains = ['sofang.com']
    start_urls = ['http://gz.sofang.com/bsrent/area/']

    rules = (
        Rule(LinkExtractor(allow=r'/bsrent/area/b', restrict_xpaths=("//div[@class='page_nav']/ul/li")), follow=True),
        Rule(LinkExtractor(allow=r'/housedetail/sr', restrict_xpaths=("//div[@class='list list_free']/dl")), follow=False, callback="parse_item"),
    )

    def parse_item(self, response):
        url = response.url
        city = re.search("//(\w+).sofang.com", url).group(1)
        title = response.xpath("//p[@class='house_name']/text()").get()
        price = response.xpath("//p[@class='total']/span/text()").get()
        hx = str(response.xpath("//div[@class='info']/dl[1]/dt/text()").getall())
        hx = hx.replace(" ", "")
        hx = hx.replace("\\r\\n", "")
        floor = response.xpath("//div[@class='info']/dl[1]/dd/text()").get()
        area = response.xpath("//div[@class='info']/dl[2]/dt/text()").get()
        decorating = response.xpath("//div[@class='info']/dl[2]/dd/text()").get()
        chaoxiang = response.xpath("//div[@class='info']/dl[3]/dt/text()").get()
        year = response.xpath("//div[@class='info']/dl[3]/dd/text()").get()
        house_name = response.xpath("//ul[@class='msg']/li/a/text()").get()
        address = response.xpath("//ul[@class='msg']/li[2]/span/text()").getall()
        address = " ".join(map(lambda x:x.strip(), address))

        try:
            coordinate = str(response.xpath("//li[@class='no_float'][2]/a/@href").get())
            coordinate = re.search("longitude=(\d+.\d+)&latitude=(\d+.\d+)", coordinate)
            longtidue = coordinate.group(1)
            latitude = coordinate.group(2)
        except:
            longtidue = None
            latitude = None

        items = SofangItem(title=title,
                           city = city,
                           price=price,
                           floor=floor,
                           decorating=decorating,
                           chaoxiang=chaoxiang,
                           area = area,
                           url=url,
                           hx=hx,
                           year=year,
                           house_name=house_name,
                           address=address,
                           longtidue=longtidue,
                           latitude=latitude,
                           date = SofangBsrentSpider.date)

        yield items
