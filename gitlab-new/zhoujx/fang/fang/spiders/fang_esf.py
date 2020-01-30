# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import datetime
from fang.items import FangItem_esf
import re
from urllib import parse

class FangEsfSpider(CrawlSpider):
    date = datetime.datetime.now().strftime('%Y-%m-%d-%H')
    custom_settings = {
        'ITEM_PIPELINES' : {'fang.pipelines.Fang_esfPipeline': 300,}
    }
    name = 'fang_esf'
    allowed_domains = ['fang.com']
    start_urls = [
                  # 'https://gz.esf.fang.com/house-a084-b017043/',  #广州
                  # 'https://fs.esf.fang.com/house-a0617-b014193/',   #佛山              #佛山
                  # 'https://sz.esf.fang.com/house-a090-b0351/',   #深圳
                  # 'https://dg.esf.fang.com/house-a097-b03076/',    #东莞

                  'https://huzhou.esf.fang.com/house-a011716-b013154/', #湖州  8162条数据
                  'https://jx.esf.fang.com/house-a011923/',   #嘉兴 4万9条
                   'https://suzhou.esf.fang.com/house-a0283-b04034/' #苏州

                  # 'https://yueyang.esf.fang.com/house-a012765/',         #岳阳  28页
                  # 'https://zhuzhou.esf.fang.com/house-a011476/',         #株洲  100页
                  # 'https://shaoyang.esf.fang.com/house-a012753/',        #邵阳  14页
                  # 'https://loudi.esf.fang.com/house-a012826/'            #娄底  6页
                ]

    rules = (
        Rule(LinkExtractor(allow=r'/house-a', restrict_xpaths="//ul[@class='clearfix choose_screen floatl'][1]/li"), follow=True),
        Rule(LinkExtractor(allow=r'/house-a', restrict_xpaths="//li[@class='area_sq']/ul[@class='clearfix']/li"), follow=True, callback='parse_item'),
        Rule(LinkExtractor(deny=r'house-a\d+/' ,
            restrict_xpaths="//div[@class='page_al']/span"), follow=True, callback='parse_item'),
    )


    # def start_requests(self):
    #     for url in self.start_urls:
    #         yield scrapy.Request(url, callback=self.parse_item)


    def parse_item(self, response):

        divs = response.xpath("//div[@class='shop_list shop_list_4']/dl[@class='clearfix']")
        print("="*30)
        print(len(divs))

        for div in divs:
            try:
                city = response.xpath("//div[@class='newnav20141104nr']/div[@class='s2']/div/a/text()").get()
                url = div.xpath("./dd[1]/h4/a/@href").get()
                url = parse.urljoin(response.url, url)
                title = div.xpath("./dd[1]/h4/a/span/text()").get()
                xiaoqu  = div.xpath("./dd[1]/p[2]/a/text()").get()
                xiaoqu = xiaoqu.strip()
                address = div.xpath("./dd[1]/p[2]/span/text()").get()
                price = div.xpath("./dd[2]/span[1]//text()").getall()
                price = " ".join(price)
                price_per = div.xpath("./dd[2]/span[2]/text()").get()


                item = FangItem_esf(
                                    date=FangEsfSpider.date,
                                    city=city,
                                    url=url,
                                    title=title,
                                    xiaoqu = xiaoqu,
                                    address=address,
                                    price=price,
                                    price_per=price_per,
                                    )
            except:
                print("出错")

            yield item

