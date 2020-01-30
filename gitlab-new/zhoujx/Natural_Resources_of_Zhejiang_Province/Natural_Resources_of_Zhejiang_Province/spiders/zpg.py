# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class ZpgSpider(CrawlSpider):
    name = 'zpg'
    allowed_domains = ['gov.cn']
    start_urls = [
        # 湖州
        # 'http://www.zjdlr.gov.cn/module/search/index.jsp?vc_name=&field_19831=%E6%B9%96%E5%B7%9E&c_createtime_start=2015-01-01&c_createtime_end=2019-08-18&strSelectID=19793%2C19831%2C19795&i_columnid=1071194&field=vc_name%3A1%2Cc_createtime%3A3%2Cfield_19831%3A1&initKind=FieldForm&currentplace=&splitflag=&fullpath=0&download=%E6%9F%A5%E8%AF%A2',
        # '        # 嘉兴
        'http://www.zjdlr.gov.cn/module/search/index.jsp?vc_name=&field_19831=%E5%98%89%E5%85%B4&c_createtime_start=2015-01-01&c_createtime_end=2019-08-18&strSelectID=19793%2C19831%2C19795&i_columnid=1071194&field=vc_name%3A1%2Cc_createtime%3A3%2Cfield_19831%3A1&initKind=FieldForm&currentplace=&splitflag=&fullpath=0&download=%E6%9F%A5%E8%AF%A2'        
        # 苏州
        ''
    ]

    rules = (
        Rule(LinkExtractor(restrict_xpaths="//div[@class='digg']"), follow=True),
        Rule(LinkExtractor(allow=r'_\d+_\d+.html', restrict_xpaths='//tr/td[@align and @class][2]/a'), callback='parse_item', follow=True),
    )

    def parse_item(self, response):

        trs = response.xpath("//div[@id='zoom']//tr/td/table/tr")
        for tr in trs[1:]:
            td = tr.xpath("./td")
            item = {}
            try:
                item['网站'] = response.url
                item['标题'] = response.xpath("//td[@class='title' and @style]/text()").get()


                # td = response.xpath("//td/table/tr[2]/td")
                item['地块编号']            = td[0].xpath("./text()").get()
                item['地块位置']        = td[1].xpath("./text()").get()
                item['土地面积(公顷)']        = td[2].xpath("./text()").get()
                item['土地用途']  = td[3].xpath("./text()").get()
                item['出让年限']        = td[4].xpath("./text()").get()
                item['成交价(万元)']        = td[5].xpath("./text()").get()
                item['受让单位']    = td[6].xpath("./text()").get()

                try:
                    item['项目名称']        = td[7].xpath("./text()").get()
                except:
                    pass
            except:
                pass

            yield item
