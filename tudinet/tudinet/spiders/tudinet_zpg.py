# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import datetime
import re

class TudinetZpgSpider(CrawlSpider):
    date = datetime.datetime.now().strftime('%Y-%m-%d-%H')

    name = 'tudinet_zpg'
    allowed_domains = ['tudinet.com']
    start_urls = [
        'https://www.tudinet.com/market-213-0-0-0/',   #广州
      # 'https://www.tudinet.com/market-98-0-0-0/',  #嘉兴 11594条数据
      # 'https://www.tudinet.com/market-99-0-0-0/',  #湖州 7710条数据
      # 'https://www.tudinet.com/market-85-0-0-0/',  #苏州 15337条数据
    ]

    rules = (
        # Rule(LinkExtractor(allow=r'market-(\d){4}-', restrict_xpaths="//ul[@class='td-city filter-ul fl-area'][2]"), follow=True),
        Rule(LinkExtractor(allow=r'market-(.*?)-pg[1-4]?[0-9].html', restrict_xpaths="//div[@class='paging clearfix']"), follow=True),
        Rule(LinkExtractor(allow=r'market-', restrict_xpaths="//div[@class='land-l-cont']/dl/dt"), follow=False, callback='parse_item'),
    )

    def parse_item(self, response):

        item = {}
        item['url'] = response.url
        # item['date'] = TudinetZpgSpider.date

        item['标题'] = response.xpath("//h3[@class='hh-name'][1]/text()").get()
        #地块编号
        item['地块编号'] = response.xpath("//div[@class='hh-info']/div[@class='hh-text']/text()").get()

        #土地基本信息
        div1 = response.xpath("//ul[@class='row hh-sort-text'][1]")
        item['所在地'] = div1.xpath("./li[1]/span/span/a/text()").getall()
        item['所在地'] = " ".join(item['所在地'])
        item['规划用途'] = div1.xpath("./li[2]/span/span/text()").get()
        item['总面积'] = div1.xpath("./li[3]/span//text()").getall()
        item['总面积'] = " ".join(item['总面积'])
        item['建设用地面积'] = div1.xpath("./li[4]/span//text()").getall()
        item['建设用地面积'] = " ".join(item['建设用地面积'])
        item['规划用地面积'] = div1.xpath("./li[5]/span//text()").getall()
        item['规划用地面积'] = " ".join(item['规划用地面积'])
        item['容积率'] = div1.xpath("./li[6]/span/text()").get()
        item['商业比例'] = div1.xpath("./li[7]/span/text()").get()
        item['建筑密度'] = div1.xpath("./li[8]/span/text()").get()
        item['出让年限'] = div1.xpath("./li[9]/span/text()").get()
        item['位置'] = div1.xpath("./li[10]/span/text()").get()
        item['四至'] = div1.xpath("./li[11]/span/text()").get()

        #土地基本信息
        div2 = response.xpath("//ul[@class='row hh-sort-text'][2]")
        item['交易状况'] = div2.xpath("./li[1]/span/text()").get()
        item['竞得方'] = div2.xpath("./li[2]/span/text()").get()
        item['起始日期'] = div2.xpath("./li[3]/span/text()").get()
        item['截至日期'] = div2.xpath("./li[4]/span/text()").get()
        item['成交日期'] = div2.xpath("./li[5]/span/text()").get()
        item['交易地点'] = div2.xpath("./li[6]/span/text()").get()
        item['起始价'] = div2.xpath("./li[7]/span/text()").get()
        item['成交价'] = div2.xpath("./li[8]/span/text()").get()
        item['土地单价'] = div2.xpath("./li[9]/span/text()").get()
        item['溢价率'] = div2.xpath("./li[10]/span/text()").get()
        item['推出楼面价'] = div2.xpath("./li[11]/span/text()").get()
        item['成交楼面价'] = div2.xpath("./li[12]/span/text()").get()
        item['保证金'] = div2.xpath("./li[13]/span/text()").get()
        item['最小加价幅度'] = div2.xpath("./li[14]/span/text()").get()
        item['公告日期'] = div2.xpath("./li[15]/span/text()").get()
        item['公告编号'] = div2.xpath("./li[16]/span/text()").get()
        item['备注'] = div2.xpath("./li[17]/span/text()").get()
        item['咨询电话'] = div2.xpath("./li[18]/span/text()").get()
        try:
            item['经度'] =  re.search("bd_x = (.*);", response.text).group(1)
            item['纬度'] =  re.search("bd_y = (.*);", response.text).group(1)
        except:
            item['经度'] = None
            item['纬度'] = None


        # 另一种页面
        # https://www.tudinet.com/market-99/view-s-481873.html
        if None is item['地块编号']:
            #
            item = {}
            item['url'] = response.url
            # item['date'] = TudinetZpgSpider.date
            item['标题'] = response.xpath("//h3[@class='hh-name'][1]/text()").get()

            div1 = response.xpath("//ul[@class='row hh-sort-text'][1]")
            item['所在地'] = div1.xpath("./li[1]/span/span/a/text()").getall()
            item['所在地'] = " ".join(item['所在地'])
            item['总面积'] = div1.xpath("./li[3]/span//text()").getall()
            item['总面积'] = " ".join(item['总面积'])
            item['规划用途'] = div1.xpath("./li[4]/span/text()").get()
            item['容积率'] = div1.xpath("./li[9]/span/text()").get()
            item['位置'] = div1.xpath("./li[10]/span/span/text()").get()
            # 土地基本信息
            div2 = response.xpath("//ul[@class='row hh-sort-text'][2]")
            item['交易状况'] = div2.xpath("./li[1]/span/text()").get()
            item['成交价'] = div2.xpath("./li[4]/span/text()").get()

        yield item
