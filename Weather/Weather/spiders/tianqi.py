# -*- coding: utf-8 -*-
import scrapy
import re
from Weather.items import WeatherItem
from datetime import datetime

class TianqiSpider(scrapy.Spider):
    name = 'tianqi'
    allowed_domains = ['tianqi.com']
    start_urls = ['http://www.tianqi.com/guangzhou/30/']
    urls = [
        'http://www.tianqi.com/foshan/30/',
        'http://www.shenzhen.com/foshan/30/'
            ]

    def parse(self, response):
        days = response.xpath("//div[@class='box_day']//div")
        city = response.xpath("//div[@class='tit_img01']//h1/text()").get()
        city = city[:2]
        year = str(datetime.now().year)


        for day in days:
            date_and_week = day.xpath(".//h3//text()").getall()
            if " " in date_and_week:
                date_and_week.remove(" ")
            date = date_and_week[0]
            date = re.findall(("\d+"), date)
            date = "".join(date)
            date = year + date

            week = date_and_week[1]
            temp = day.xpath(".//ul/li[@class='temp']//text()").getall()
            temp = "".join(temp)
            condition = temp.split(" ")[0]
            min = temp.split(" ")[1].split("~")[0]
            max = temp.split(" ")[1].split("~")[1]
            max = re.match('\d+', max).group()

            # wind = day.xpath(".//ul/li")[-1]
            # wind = wind.xpath(".//text()").get()
            item = WeatherItem(date=date, max=max, min=min, city=city, condition=condition)

            yield item


        yield scrapy.Request(url='http://www.tianqi.com/foshan/30/', callback=self.parse)
        yield scrapy.Request(url='http://www.tianqi.com/shenzhen/30/', callback=self.parse)



