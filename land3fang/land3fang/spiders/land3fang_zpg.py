# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import re

class Lang3fangZpgSpider(CrawlSpider):
    name = 'land3fang_zpg'
    allowed_domains = ['3fang.com']
    start_urls = [
        'https://land.3fang.com/market/320500__1_2_____1_0_30.html',  #苏州
        # 'https://land.3fang.com/market/330500__1______1_0_1.html',  #湖州
        # 'https://land.3fang.com/market/330400__1______1_0_1.html',  #嘉兴
    ]

    rules = (
        Rule(LinkExtractor(allow=r'0_[1-2]?[0-9].html', restrict_xpaths="//div[@id='divAspNetPager']"), follow=True),
        Rule(LinkExtractor(allow=r'/market/.*html', restrict_xpaths="//div[@class='list28_text fl']/h3"), callback='parse_item', follow=False),
    )

    def parse_item(self, response):
        item = {}

        item['网站'] = response.url
        item['标题'] = response.xpath("//div[@class='tit_box01']/text()").get()
        item['地块编号'] = response.xpath("//div[@class='menubox01 mt20']/span/text()").get()

        ####
        try:
            coordinate = response.xpath("//iframe[@id='mapframe']/@src").get()
            coordinate_x = re.search(".*pointx=(\d+\.\d+)&pointy=(\d+\.\d+)", coordinate).group(1)
            coordinate_y = re.search(".*pointx=(\d+\.\d+)&pointy=(\d+\.\d+)", coordinate).group(2)
            item['经度'] = coordinate_x
            item['维度'] = coordinate_y
        except:
            print("出错")
            print(response.url)
            item['经度'] = coordinate_x
            item['纬度'] = coordinate_y

        ####
        trs = response.xpath("//table[@class='tablebox02 mt10']")[0].xpath("./tbody/tr")
        item['地区'] = trs[0].xpath("./td[1]/a/text()").get()
        item['所在地'] = trs[0].xpath("./td[2]/a/text()").get()
        item['总面积'] = trs[1].xpath("./td[1]/em/text()").get()+ trs[1].xpath("./td[1]/text()").get()
        item['建设用地面积'] = trs[1].xpath("./td[2]/em/text()").get() + trs[1].xpath("./td[2]/text()").get()
        item['规划建筑面积'] = trs[2].xpath("./td[1]/em/text()").get() + trs[2].xpath("./td[1]/text()").get()
        item['代征面积'] = trs[2].xpath("./td[2]/em/text()").get()
        item['容积率'] = trs[3].xpath("./td[1]/text()").get()
        item['绿化率'] = trs[3].xpath("./td[2]/text()").get()
        item['商业比例'] = trs[4].xpath("./td[1]/text()").get()
        item['建筑密度 '] = trs[4].xpath("./td[2]/text()").get()
        item['限制高度'] = trs[5].xpath("./td[1]/text()").get()
        item['出让形式'] = trs[5].xpath("./td[2]/text()").get()
        item['出让年限'] = trs[6].xpath("./td[1]/text()").get()
        item['位置'] = trs[6].xpath("./td[2]/text()").get()
        item['四至'] = trs[7].xpath("./td[1]/text()").get()
        item['规划用途'] = trs[7].xpath("./td[2]/a/text()").get()

        ####
        trs = response.xpath("//table[@class='tablebox02 mt10']")[1].xpath("./tbody/tr")
        item['交易状况'] = trs[0].xpath("./td[1]/text()").get()
        item['起始日期'] = trs[1].xpath("./td[1]/text()").get()
        item['截至日期'] = trs[1].xpath("./td[2]/text()").get()

        #部分城市才有
        item['竞得方'] = trs[0].xpath("./td[2]/text()").get()
        item['成交价'] = trs[3].xpath("./td[2]/text()").get()


        return item
