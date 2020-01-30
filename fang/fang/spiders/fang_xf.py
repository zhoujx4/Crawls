# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import re
import datetime

class FangXfSpider(CrawlSpider):
    date = datetime.datetime.now().strftime('%Y-%m-%d-%H')
    custom_settings = {
        'ITEM_PIPELINES' : {'fang.pipelines.Fang_xfPipeline': 300,}
    }
    name = "fang_xf"
    allowed_domains = ["fang.com"]
    start_urls = [
                  'https://heyuan.newhouse.fang.com/house/s/a73/',  #汕头
                  # 'https://fs.newhouse.fang.com/house/s/',
                  # 'https://dg.newhouse.fang.com/house/s/',
                  # 'https://sz.newhouse.fang.com/house/s/',
                ]
    pattern = re.compile('[\t|\n]')

    rules = (
        Rule(LinkExtractor(allow=r'.*/house/s/', restrict_xpaths="//li[@class='fr']"), follow=True),
        Rule(LinkExtractor(restrict_xpaths="//div[@id='newhouse_loupai_list']//div[@class='nlcd_name']"), callback="parse_item", follow = False),
    )

    def parse_item(self, response):


        item = {}

        #### 不同页面不同
        item['楼盘类型'] = '别墅'

        item['楼盘名'] = response.xpath("//div[@class='tit']/h1/strong/text()").get()
  #      if item['楼盘名'] is None:
  #          item['楼盘名'] = response.xpath("//h1[@class='lp-name']/span/text()").get()
        item['城市'] = response.xpath("//div[@class='newnav20141104nr']/div[@class='s2']/div/a/text()").get()
        item['区'] = response.xpath("//div[@class='br_left']/div/ul/li[3]/a/text()").get()[:2]
        item['网站'] = response.url
        item['主力户型'] = response.xpath("//h3[contains(text(),'主力户型')]/following-sibling::div/a//text()").getall()
        if item['主力户型'] is not None:
            item['主力户型'] = " ".join(item['主力户型'])

        #楼栋信息
        dict_longdong = {}
        Info_longdongs = response.xpath("//div[@class='fr']/div[@class='dongInfo']")
        for Info_longdong in Info_longdongs:
            name_longdong = Info_longdong.xpath("./div/@class").get()
            name_long = re.search("\d+", name_longdong).group()
            name_longdong = response.xpath("//div[@class='fr']/div/div/span[contains(@class,{})]/text()".format(name_long)).get()

            dict_set = {}
            dict_set['单元'] = Info_longdong.xpath("./div/ul/li[1]/text()").get()
            dict_set['电梯数'] = Info_longdong.xpath("./div/ul/li[2]/text()").get()
            dict_set['建筑类型'] = Info_longdong.xpath("./div/ul/li[3]/text()").get()
            dict_set['楼层'] = Info_longdong.xpath("./div/ul/li[4]/text()").get()
            dict_set['户数'] = Info_longdong.xpath("./div/ul/li[5]/text()").get()
            dict_set['在售房源'] = Info_longdong.xpath("./div/ul/li[6]/text()").get()

            hxs = Info_longdong.xpath("./div/div[@class='hx']/ul/li")
            hxs_list = []
            for hx in hxs:
                each_hx =  hx.xpath("./a/span/text()").getall()
                each_hx = list(map(lambda x:re.sub("\t|\n", "", x), each_hx))
                hxs_list.append(each_hx)
            dict_set['户型'] = hxs_list
            dict_longdong[name_longdong] = dict_set
        dict_longdong = str(dict_longdong)
        item['楼栋信息'] = dict_longdong
        #房价走势
        try:
            item['房价走势'] = re.search('\"house\","data":\[(\[.*?)\]},', response.text).group(1)
        except:
            item['房价走势'] = '暂无数据'


        # yield item
        #进楼盘详情页面
        #https://jinshadaduhuibl.fang.com/house/2811173536/housedetail.htm
        housedetail = response.xpath("//div[@id='orginalNaviBox']/a[2]/@href").get()
        if not housedetail:
            print('转到详情页出问题了，出问题的网站是')
            print(response.url)
        housedetail = "https:" + housedetail

        yield scrapy.Request(url=housedetail, callback=self.parse_detail, meta={'item':item})


    def parse_detail(self, response):

        #通过response获取item
        item = response.meta['item']


        # #### 基本信息
        item['价格'] = response.xpath("//div/span[text()='价']/following-sibling::em/text()").get().strip()
        item['项目特色'] = response.xpath("//div[contains(text(),'项目特色') or contains(text(),'楼盘特色')]/following-sibling::div/span/text()").getall()
        if item['项目特色'] is not None:
            item['项目特色'] = " ".join(item['项目特色'])
        item['装修状况'] = response.xpath("//div[contains(text(),'装修情况') or contains(text(),'装修状况')]/following-sibling::div/text()").get().strip()
        item['产权年限'] = response.xpath("//div[contains(text(),'产权年限')]/following-sibling::div//text()").getall()
        item['产权年限'] = " ".join([x.strip() for x in item['产权年限']]).strip()
        item['开发商']   = response.xpath("//div[text()='开' and @class='list-left']/following-sibling::div/a/text()").get()
        item['楼盘地址'] = response.xpath("//div[contains(text(),'楼盘地址')]/following-sibling::div/text()").get().strip()


        #### 销售情况
        item['销售状态'] = response.xpath("//div[contains(text(),'销售状态')]/following-sibling::div/text()").get().strip()
        item['开盘时间'] = response.xpath("//div[contains(text(),'开盘时间')]/following-sibling::div/text()").get()
        item['交房时间'] = response.xpath("//div[contains(text(),'交房时间')]/following-sibling::div/text()").get()

        ########################################################################################################################
        ########################################################################################################################
        ########################################################################################################################
        ########################################################################################################################
        try:
            trs = response.xpath("//div[@class='main-item']")[1].xpath(".//table[@cellpadding]")[1].xpath("./tr")
            item['预售信息'] = []
            for tr in trs[1:]:
                dict = {}
                dict['预售许可证'] = tr.xpath("./td[1]/text()").get()
                dict['发证时间'] = tr.xpath("./td[2]/text()").get()
                dict['绑定楼栋'] = tr.xpath("./td[3]/text()").get()
                item['预售信息'].append(dict)
        except:
            item['预售信息'] = "暂无资料"

        # #### 小区规划
        item['占地面积']    = response.xpath("//div[contains(text(),'占地面积')]/following-sibling::div//text()").get()
        item['建筑面积']    = response.xpath("//div[contains(text(),'建筑面积')]/following-sibling::div//text()").get()
        item['容积率']      = response.xpath("//div[text()='容' and @class='list-left']/following-sibling::div/text()").get()
        item['绿化率']      = response.xpath("//div[text()='绿' and @class='list-left']/following-sibling::div/text()").get()
        item['停车位']      = response.xpath("//div[contains(text(),'停') and @class='list-left']/following-sibling::div/text()").get()
        item['物业公司']    = response.xpath("//div[contains(text(),'物业公司')]/following-sibling::div/a/text()").get()
        item['楼层状况']    = response.xpath("//div[contains(text(),'楼层说明') or contains(text(),'楼层状况')]/following-sibling::div//text()").get()
        item['物业费']      = response.xpath("//div[(text()='物' or text()='物业费：') and @class='list-left']/following-sibling::div/text()").get()
        item['楼栋总数']    = response.xpath("//div[contains(text(),'楼栋总数')]/following-sibling::div/text()").get()
        item['总户数']      = response.xpath("//div[text()='总' and @class='list-left']/following-sibling::div/text()").get()
        item['物业费描述']  = response.xpath("//div[contains(text(),'物业费描述')]/following-sibling::div//text()").get()

        #楼盘动态开盘信息
        #https://lantingshenghui.fang.com/house/2812281986/dongtai.htm
        gushi_open = response.xpath("//a[(text()='动态') or (text()='楼盘动态')]/@href").get()
        if not gushi_open:
            print('转到楼盘动态页问题了，出问题的网站是')
            print(response.url)
        gushi_open = "https:" + gushi_open
        print(gushi_open)
        yield scrapy.Request(url=gushi_open, callback=self.parse_kaipan_detail, meta={'item':item})

    def parse_kaipan_detail(self, response):
        item = response.meta['item']
      
        lis = response.xpath("//div[@id='gushi_open']/ul/li")
        tmp = []
        for li in lis:
            info_kaipan = {}
            info_kaipan['日期'] = li.xpath("./div/text()").get().strip()
            info_kaipan['开盘时间'] = li.xpath("./p[contains(text(),'开盘时间')]/text()").get()
            info_kaipan['开盘楼栋'] = li.xpath("./p[contains(text(),'开盘楼栋')]/text()").get()
            info_kaipan['开盘详情'] = li.xpath("./p[contains(text(),'开盘详情')]/text()").get()
            tmp.append(info_kaipan)
        item['开盘时间轴'] = tmp
        print('到了')


        yield item




