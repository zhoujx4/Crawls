# -*- coding: utf-8 -*-

#搜房网租房-整租频道：http://gz.sofang.com/esfrent/area/aa1135-bl1

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from sofang.items import SofangItem
import datetime
import re




class SofangEsfrentSpider(CrawlSpider):
    date = datetime.datetime.now().strftime('%Y-%m-%d-%H')
    custom_settings = {
        'ITEM_PIPELINES' : {'sofang.pipelines.EsfrentPipeline': 300,}
    }
    name = 'sofang_esfrent'
    allowed_domains = ['sofang.com']
    start_urls = ['http://gz.sofang.com/esfrent/area/']

    rules = (
        Rule(LinkExtractor(allow=r'/esfrent/area/aa\d+', restrict_xpaths="//div[@class='search_info']/dl[1]/dd[1]"),  follow=True), #区
        Rule(LinkExtractor(allow=r'/esfrent/area/aa',restrict_xpaths="//div[@class='page_nav']/ul/li"), follow=True),  #页面
        Rule(LinkExtractor(allow=r'/housedetail/sr\d+.html', restrict_xpaths="//dd[@class='house_msg']/p[@class='name']"), follow=False, callback="parse_item"),
    )

    def parse_item(self, response):
        url = response.url
        title = response.xpath("//p[@class='house_name']/text()").get()
        price = response.xpath("//p[@class='total']/span/text()").getall()
        price = " ".join(price)
        price_mean = response.xpath("//p[@class='averages']/text()").get()
        hx = response.xpath("//div[@class='info']/dl[1]/dt/text()").getall()
        hx = str(hx)
        hx = hx.replace(" ", "")
        hx = hx.replace("\r\n", "")
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
                           price=price,
                           price_mean=price_mean,
                           decorating=decorating,
                           chaoxiang=chaoxiang,
                           area = area,
                           url=url,
                           floor=floor,
                           hx=hx,
                           year=year,
                           house_name=house_name,
                           address=address,
                           longtidue=longtidue,
                           latitude=latitude,
                           date = SofangEsfrentSpider.date)

        yield items
