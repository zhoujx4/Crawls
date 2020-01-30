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
                  'https://gz.newhouse.fang.com/house/s/',  #广州 586条
                  # 'https://fs.newhouse.fang.com/house/s/',
                  # 'https://dg.newhouse.fang.com/house/s/',
                  # 'https://sz.newhouse.fang.com/house/s/',

                  # 'https://jx.newhouse.fang.com/house/s/',               #嘉兴   #208条数据
                  # "https://huzhou.newhouse.fang.com/house/s/",            #湖州    #296条数据
                  # 'https://suzhou.newhouse.fang.com/house/s/',   #苏州   408条数据

                  # 'https://nt.newhouse.fang.com/house/s/',             #南通
                  # 'https://suzhou.newhouse.fang.com/house/s/',         #苏州
                  # 'https://wuxi.newhouse.fang.com/house/s/',           #无锡
                  # 'https://nanjing.newhouse.fang.com/house/s/'         #南京
                ]
    pattern = re.compile('[\t|\n]')

    rules = (
        Rule(LinkExtractor(allow=r'.*/house/s/b\d+', restrict_xpaths="//li[@class='fr']"), follow=True),
        Rule(LinkExtractor(restrict_xpaths="//div[@id='newhouse_loupai_list']//div[@class='nlcd_name']"), callback="parse_item", follow = False),
    )

    def parse_item(self, response):
        '''
        title：名称
        price：均价
        huxing：主力户型
        adddress：项目地址
        kaipan： 近期开盘
        '''
        item = {}
        item['城市'] = response.xpath("//div[@class='newnav20141104nr']/div[@class='s2']/div/a/text()").get()
        item['网站'] = response.url
        item['楼盘名'] = response.xpath("//div[@class='tit']/h1/strong/text()").get()
        item['价格'] = response.xpath("//div[@class='inf_left fl ']/span/text()").get()

        item['项目地址'] = response.xpath("//div[@class='inf_left fl']/span/text()").get()

        #https://dinghuixfg.fang.com/
        if None is item['楼盘名']:
            item['楼盘名'] = response.xpath("//div[@class='lp-info']/h1[@class='lp-name']/span/text()").get()
            item['价格'] = response.xpath("//div[@class='lp-info']/div[@class='l-price']/strong/text()").get()
            item['近期开盘'] = response.xpath("//div[@class='lp-info']/div[@class='lp-type'][3]/span/a/text()").get()
            item['项目地址'] = response.xpath("//div[@class='lp-info']/div[@class='lp-type'][4]/span/i/text()").get()




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
            item['房价走势'] = re.search('data":\[(\[.*?)\]},',response.text).group(1)
        except:
            pass

        # yield item
        #进楼盘详情页面
        #https://jinshadaduhuibl.fang.com/house/2811173536/housedetail.htm
        housedetail = response.xpath("//div[@id='orginalNaviBox']/a[2]/@href").get()
        if not housedetail:
            print('出问题了，出问题的网站是')
            print(response.url)
        housedetail = "https:" + housedetail

        yield scrapy.Request(url=housedetail, callback=self.parse_detail, meta={'item':item})

    def parse_detail(self, response):


        #通过response获取item
        item = response.meta['item']

        # 基本信息
        print(response.url)
        item['物业类别'] = response.xpath("//li/div[@class='list-right']/text()").get().strip()
        item['项目特色'] = " ".join(response.xpath("//span[@class='tag']//text()").getall())
        try:
            item['建筑类别'] = re.sub(FangXfSpider.pattern, '', response.xpath(".//span[@class='bulid-type']/text()").get())
            item['装修状况'] = re.sub(FangXfSpider.pattern, '', response.xpath("//li/div[@class='list-right']")[3].xpath("./text()").get())
        except:
            item['建筑类别'] = None
            item['装修状况'] = None
        item['财产年限'] = response.xpath("//div[@class='clearfix cqnx_512']/p/text()").get()
        item['开发商'] = response.xpath("//div[@class='list-right-text']/a[@href and @target='_blank']/text()").get()

        #销售情况
        div = response.xpath("//div[@class='main-item']")[1].xpath("./ul/li")
        item['销售状态'] = div[0].xpath("./div[@class='list-right']/text()").get()
        item['开盘时间'] = div[2].xpath("./div[@class='list-right']/text()").get()
        item['交房时间'] = div[3].xpath("./div[@class='list-right']/text()").get()
        item['主力户型'] = div[6].xpath("./div[@class='list-right-text']//text()").getall()
        item['主力户型'] = " ".join(map(lambda x:x.strip(), item['主力户型']))
        trs = div.xpath("//table[@cellpadding]")[1].xpath("./tr")
        item['预售信息'] = []
        for tr in trs[1:]:
            dict = {}
            dict['预售许可证'] = tr.xpath("./td[1]/text()").get()
            dict['发证时间'] = tr.xpath("./td[2]/text()").get()
            dict['绑定楼栋'] = tr.xpath("./td[3]/text()").get()
            item['预售信息'].append(dict)


        # 小区规划
        div = response.xpath("//div[@class='main-item'][3]/ul/li")
        item['占地面积'] = div[0].xpath("./div[@class='list-right']/text()").get()
        item['建筑面积'] = div[1].xpath("./div[@class='list-right']/text()").get()
        try:
            item['容积率'] = div[2].xpath("./div[@class='list-right']/text()").get()
            item['绿化率'] = div[3].xpath("./div[@class='list-right']/text()").get()
            item['停车位'] = div[4].xpath("./div[@class='list-right']/text()").get()
            item['楼栋总数'] = div[5].xpath("./div[@class='list-right']/text()").get()
            item['总户数'] = div[6].xpath("./div[@class='list-right']/text()").get()
            item['物业公司'] = div[7].xpath("./div[@class='list-right']/a/text()").get()
            item['物业费'] = div[8].xpath("./div[@class='list-right']/text()").get()
            item['物业费描述'] = div[9].xpath("./div[@class='list-right-floor']/text()").get()
            item['楼层状况'] = div[10].xpath("./div[@class='list-right-floor']/text()").get()
        except:
            print('test')
            item['容积率'] = div[6].xpath("./div[@class='list-right']/text()").get()
            item['绿化率'] = div[8].xpath("./div[@class='list-right']/text()").get()

        yield item

