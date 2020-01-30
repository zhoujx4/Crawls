# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class FangZfSpider(CrawlSpider):
    custom_settings = {
        'ITEM_PIPELINES' : {'fang.pipelines.Fang_zfPipeline': 300,}
    }
    name = 'fang_zf'
    allowed_domains = ['fang.com']
    start_urls = ['https://xt.zu.fang.com/']

    rules = (
        # Rule(LinkExtractor(allow=r'/house/i'), restrict_xpaths='//dd[@style='position']/a' ,callback='parse_item', follow=True),
        Rule(LinkExtractor(allow=r'/house/i', restrict_xpaths="//div[@class='fanye']/a"), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        dls = response.xpath("//div[@class='houseList']/dl")
        for dl in dls:
            item = {}
            item['城市'] = '湘潭市'
            item['地址'] = dl.xpath("./dd[@class='info rel']/p[3]//text()").getall()
            item['地址'] = "".join(item['地址'])
            item['地址'] = item['地址'].replace("-", "")
            print(item)            
            item['网址'] = response.url[:-1] + dl.xpath("./dd[@class='info rel']/p[@class='title']/a/@href").get()
            item['标题'] = dl.xpath("./dd[@class='info rel']/p[@class='title']/a/text()").get()
            tmp = dl.xpath("./dd[@class='info rel']/p[2]//text()").getall()
            while "|" in tmp:
                tmp.remove("|")
            print(tmp)
            item['方式'] = tmp[0].strip()
            item['户型'] = tmp[1].strip()
            item['面积'] = tmp[2].strip()
            item['价钱'] = dl.xpath("./dd[@class='info rel']/div[@class='moreInfo']/p//text()").getall()
            item['价钱'] = "".join(item['价钱'])
            # item['朝向'] = tmp[3]
            yield item
