# coding=utf-8 

'''
Author: 周俊贤
Email：673760239@qq.com

date:2019/8/11 10:50
'''
from selenium import webdriver
from lxml import etree
import time
import re
from selenium.webdriver.chrome.options import Options
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import datetime
import os
import json
import sys

# 广东
'''
广州 = [
                "https://gz.zu.fang.com/house-a080/",             #增城 45页
                "https://gz.zu.fang.com/house-a078/g21/",           #番禺 一居 29页
                "https://gz.zu.fang.com/house-a078/g22/",          #番禺 二居 54页
                "https://gz.zu.fang.com/house-a078/g23/",           #番禺 三居 66页
                "https://gz.zu.fang.com/house-a078/g24/",           #番禺 四居 21页
                "https://gz.zu.fang.com/house-a078/g299/",           #番禺 四居以上 13页
                "https://gz.zu.fang.com/house-a084/",                 #南沙 40页
                "https://gz.zu.fang.com/house-a0639/",                #花都 26页
                "https://gz.zu.fang.com/house-a076/g21/",               #白云 一居 23页
                "https://gz.zu.fang.com/house-a076/g22/",               #白云 二居 40页
                "https://gz.zu.fang.com/house-a076/g23/",                #白云 三居 39页
                "https://gz.zu.fang.com/house-a076/g24/",                #白云 四居 9页
                "https://gz.zu.fang.com/house-a076/g299/",                   #白云 四居以上 3页
                "https://gz.zu.fang.com/house-a074/g21/",                #海珠 一居 36页
                "https://gz.zu.fang.com/house-a074/g22/",                    #海珠 二居 83页
                "https://gz.zu.fang.com/house-a074/g23/",                   #海珠 三居 58页
                "https://gz.zu.fang.com/house-a074/g24/",                   #海珠 四居 19页 
                "https://gz.zu.fang.com/house-a074/g299/",                   #海珠 四居以上 7页
                "https://gz.zu.fang.com/house-a072/g21/",                      #越秀 一居 46页 
                "https://gz.zu.fang.com/house-a072/g22/",                    #越秀 二居 100页
                "https://gz.zu.fang.com/house-a072/g23/",                       #越秀 三居 65页
                "https://gz.zu.fang.com/house-a072/g24/",                  #越秀 四居 7页
                "https://gz.zu.fang.com/house-a072/g299/",                         #越秀 四居以上 4页
                "https://gz.zu.fang.com/house-a071/",                   #荔湾 72页 
                "https://gz.zu.fang.com/house-a073/g21/",                  #天河 一居 100页
                "https://gz.zu.fang.com/house-a073/g22/",                   #天河 二居 100页
                "https://gz.zu.fang.com/house-a073/g23/",               #天河 三居 100页
                "https://gz.zu.fang.com/house-a073/g24/",            #天河 四居 33页
                "https://gz.zu.fang.com/house-a073/g299/",              #天河 四居以上 10页
                "https://gz.zu.fang.com/house-a079/",               #从化 3页
                "https://gz.zu.fang.com/house-a075/",             #黄埔 86页
                "https://gz.zu.fang.com/house-a015882/",       #广州周边 10页
]

"https://fs.zu.fang.com/" #佛山 84页

深圳 = [
        "https://sz.zu.fang.com/house-a090/g21/"  #深圳 龙岗 一居 54页
        "https://sz.zu.fang.com/house-a090/g22/"  #深圳 龙岗 二居 41页
        "https://sz.zu.fang.com/house-a090/g23/"  #深圳 龙岗 三居 53页
        "https://sz.zu.fang.com/house-a090/g24/"  #深圳 龙岗 四居 18页
        "https://sz.zu.fang.com/house-a090/g299/" #深圳 龙岗 四居以上 7页
        "https://sz.zu.fang.com/house-a013080/g21/" #深圳 龙华 一居 35页
        "https://sz.zu.fang.com/house-a013080/g22/“ #深圳 龙华 二居 19页
        "https://sz.zu.fang.com/house-a013080/g23/" #深圳 龙华 三居 30页
        "https://sz.zu.fang.com/house-a013080/g24/" #深圳 龙华 四居 16页
        "https://sz.zu.fang.com/house-a013080/g299/" #深圳 龙华 四居以上 12页
        "https://sz.zu.fang.com/house-a089/g21/"     #深圳 宝安 一居 88页
        "https://sz.zu.fang.com/house-a089/g22/"     #深圳 宝安 二居 37页
        "https://sz.zu.fang.com/house-a089/g23/"     #深圳 宝安 三居 59页
        "https://sz.zu.fang.com/house-a089/g24/"     #深圳 宝安 四居 17页 
        "https://sz.zu.fang.com/house-a089/g299/"    #深圳 宝安 四居以上 5页
        "https://sz.zu.fang.com/house-a087/g21/"     #深圳 南山 一居 66页
        "https://sz.zu.fang.com/house-a087/g22/"     #深圳 南山 二居 100页
        "https://sz.zu.fang.com/house-a087/g23/"     #深圳 南山 三居 100页
        "https://sz.zu.fang.com/house-a087/g24/"     #深圳 南山 四居 75页
        "https://sz.zu.fang.com/house-a087/g299/"    #深圳 南山 四居以上 38页
        "https://sz.zu.fang.com/house-a085/g21/"     #深圳 福田 一居  59页
        "https://sz.zu.fang.com/house-a085/g22/"     #深圳 福田 二居  79页
        "https://sz.zu.fang.com/house-a085/g23/"     #深圳 福田 三居  99页
        "https://sz.zu.fang.com/house-a085/g24/"     #深圳 福田 四居  29页
        "https://sz.zu.fang.com/house-a085/g299/"    #深圳 福田 四居以上 9页
        "https://sz.zu.fang.com/house-a086/g21/"     #深圳 罗湖 一居  41页
        "https://sz.zu.fang.com/house-a086/g22/"     #深圳 罗湖 二居  44页
        "https://sz.zu.fang.com/house-a086/g23/"     #深圳 罗湖 三居  36页
        "https://sz.zu.fang.com/house-a086/g24/"     #深圳 罗湖 四居  8页
        "https://sz.zu.fang.com/house-a086/g299/"    #深圳 罗湖 四居以上 3页
        "https://sz.zu.fang.com/house-a013081/"    #深圳 坪山区 14页
        "https://sz.zu.fang.com/house-a013079/"    #深圳 光明区 14页
        "https://sz.zu.fang.com/house-a088/"       #深圳 盐田 9页
        "https://sz.zu.fang.com/house-a013082/"    #深圳 大鹏新区 4页
        "https://sz.zu.fang.com/house-a016375/"    #深圳  深圳周边 3页
        ]
东莞 = [
        "https://dg.zu.fang.com/house-a097/"     #莞城 11页
        "https://dg.zu.fang.com/house-a098/"  #东城 66页
        "https://dg.zu.fang.com/house-a099/"  #南城 38页
        "https://dg.zu.fang.com/house-a0100/"  #万江 5页 
        "https://dg.zu.fang.com/house-a0101/"  #虎门 22页
        "https://dg.zu.fang.com/house-a0102/"  #厚街 10页
        "https://dg.zu.fang.com/house-a0103/"  #樟木头 12页
        "https://dg.zu.fang.com/house-a0104/"  #常平 14页
        "https://dg.zu.fang.com/house-a0105/"  #长安 13页
        "https://dg.zu.fang.com/house-a0106/"  #石碣  4页
        "https://dg.zu.fang.com/house-a0107/"  #石龙 5页
        "https://dg.zu.fang.com/house-a0108/"  #凤岗 30页
        "https://dg.zu.fang.com/house-a0803/"  #黄江 10页
        "https://dg.zu.fang.com/house-a0110/"  #塘厦 36页
        "https://dg.zu.fang.com/house-a0805/"  #清溪 10页
        "https://dg.zu.fang.com/house-a0811/"  #茶山 3页
        "https://dg.zu.fang.com/house-a0810/"  #石排 1页
        "https://dg.zu.fang.com/house-a0809/"  #企石 1页 
        "https://dg.zu.fang.com/house-a0806/"  #桥头 2页
        "https://dg.zu.fang.com/house-a0804/"  #谢岗 1页
        "https://dg.zu.fang.com/house-a0117/"  #大朗 13页
        "https://dg.zu.fang.com/house-a0802/"  #寮步 14页
        "https://dg.zu.fang.com/house-a0808/"  #东坑 1页
        "https://dg.zu.fang.com/house-a0807/"  #横沥 3页
        "https://dg.zu.fang.com/house-a0121/"  #大岭山 7页
        "https://dg.zu.fang.com/house-a0801/"  #沙田 3页
        "https://dg.zu.fang.com/house-a0798/"  #高埗 1页
        "https://dg.zu.fang.com/house-a0796/"  #望牛墩 2页
        "https://dg.zu.fang.com/house-a0795/"  #中堂 1页
        "https://dg.zu.fang.com/house-a0797/"  #麻涌 1页
        "https://dg.zu.fang.com/house-a0799/"  #洪梅 1页
        "https://dg.zu.fang.com/house-a0800/"  #道滘 3页
        "https://dg.zu.fang.com/house-a0927/"  #松山湖 14页
        "https://dg.zu.fang.com/house-a013485/"  #东莞周边 2页
]  
    
    
'''

# 湖南
'''
"https://yueyang.zu.fang.com/",  #岳阳 4页
"https://zhuzhou.zu.fang.com/",  #株洲 13页
"https://shaoyang.zu.fang.com/",  #邵阳 2页
"https://loudi.zu.fang.com/",     #娄底 2页
'''

class Fang_zf(object):
    driver_path = r'/usr/bin/chromedriver'
    # driver_path = r'D:/chromedriver.exe'
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    PROJECT_PATH = os.getcwd()
    PROJECT_PATH = os.path.join(PROJECT_PATH, "fang_zf")



    def __init__(self):
        self.driver = webdriver.Chrome(executable_path=Fang_zf.driver_path, options = Fang_zf.chrome_options)
        self.pyname = os.path.basename(sys.argv[0]).split(".")[0]
        # self.json = open(os.path.join(Fang_zf.PROJECT_PATH, 'fang_zf{}.json'.format(datetime.now().strftime('%Y-%m-%d'))), 'a', encoding='utf-8')
        self.urls = [
            "https://fs.zu.fang.com/house/i354/"  #佛山 84页
        ]



    def parse_detail_page(self, source):
        Info = {}
        html = etree.HTML(source)
        Info['标题'] = html.xpath("//div[@class='tab-cont clearfix']/h1/text()")[0]
        #     Info['价格'] = html.xpath("//div[@class='tr-line clearfix zf_new_title']//i/text()")[0] \
        #                                 + html.xpath("//div[@class='tr-line clearfix zf_new_title']/div//text()")
        Info['价格_详情'] = html.xpath("//div[@class='tr-line clearfix zf_new_title']//text()")
        Info['价格_详情'] = " ".join(map(lambda x: x.strip(), Info['价格_详情']))
        Info['价格'] = html.xpath("//div[@class='tr-line clearfix zf_new_title']//i/text()")[0]
        Info['出租方式'] = html.xpath("//div[@class='trl-item1 w146']")[0].xpath("./div/text()")[0].strip()
        Info['朝向'] = html.xpath("//div[@class='trl-item1 w146']")[1].xpath("./div[@class='tt']/text()")[0]
        Info['户型'] = html.xpath("//div[@class='trl-item1 w182']")[0].xpath("./div[@class='tt']/text()")[0]
        Info['楼层'] = html.xpath("//div[@class='trl-item1 w182']")[1].xpath("./div[@class='tt']/text()")[0] + " " + \
                     html.xpath("//div[@class='trl-item1 w182']")[1].xpath("./div[@class='font14']/text()")[0]
        Info['建筑面积'] = html.xpath("//div[@class='trl-item1 w132']")[0].xpath("./div[@class='tt']/text()")[0]
        Info['装修'] = html.xpath("//div[@class='trl-item1 w132']")[1].xpath("./div[@class='tt']/text()")[0]
        Info['小区'] = html.xpath("//div[contains(@class,'rcont')]")[0].xpath("./a/text()")
        Info['地址'] = html.xpath("//div[contains(@class,'rcont')]")[1].xpath("./a/text()")
        #     Info['朝向'] = html.xpath("//div[@class='trl-item1 w146'][2]/div[@class='tt']/text()")[0]
        #     Info['户型'] = html.xpath("//div[@class='trl-item1 w182']/div[@class='tt']/text()")[0]
        #     Info['楼层'] = html.xpath("//div[@class='trl-item1 w182']/div/text()")
        #     Info['建筑面积'] = html.xpath("//div[@class='trl-item1 w132'][1]/div[@class='tt']/text()")[0]
        #     Info['装修'] = html.xpath("//div[@class='trl-item1 w132'][2]/div[@class='tt']/text()")[0]
        return Info

    def save_json(self, Info):
        with open(os.path.join(Fang_zf.PROJECT_PATH, '{}_{}.json'.format(self.pyname, datetime.now().strftime('%Y-%m-%d'))), 'a', encoding='utf-8') as f:
            jsonbj = json.dumps(Info, ensure_ascii=False)
            f.write("\n" + jsonbj)

    def run(self):
        self.driver.get("https://gz.zu.fang.com/")

        # 遍历所有urls
        for url in self.urls:
            self.driver.execute_script("window.open('{}')".format(url))  #这里要加一个循环
            self.driver.switch_to.window(self.driver.window_handles[1])

            try:
                next_page = self.driver.find_element_by_partial_link_text("下一页")
            except:
                next_page = None
            try:
                pages_detail = self.driver.find_elements_by_xpath("//p[@class='title']/a")
            except:
                pages_detail = None

            First_page = True #只有一页的情况
            while next_page or First_page:
                First_page = False

                print('当前爬的索引页为', self.driver.current_url)
                for page_detail in pages_detail:
                    page_detail.click()
                    self.driver.switch_to.window(self.driver.window_handles[-1])  # 跳到详情页
                    WebDriverWait(self.driver, 0.5).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, '装修')))
                    source = self.driver.page_source
                    try:
                        Info = self.parse_detail_page(source)
                    except:
                        pass
                    Info['网站'] = self.driver.current_url
                    print(Info)

                    # 保存入json文件
                    self.save_json(Info)

                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[1])  # 关闭详情页，跳回列表页
                if next_page is not None:
                    next_page.click()
                else:
                    break
                self.driver.switch_to.window(self.driver.window_handles[1])  # 跳回新的索引页
                try:
                    next_page = self.driver.find_element_by_partial_link_text("下一页")
                    pages_detail = self.driver.find_elements_by_xpath("//p[@class='title']/a")
                except:
                    next_page = None
                    print('当前爬的索引页为', self.driver.current_url)
                    try:
                        pages_detail = self.driver.find_elements_by_xpath("//p[@class='title']/a")
                    except:
                        break
                    for page_detail in pages_detail:
                        page_detail.click()
                        self.driver.switch_to.window(self.driver.window_handles[-1])  # 跳到详情页
                        WebDriverWait(self.driver, 0.5).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, '装修')))
                        source = self.driver.page_source
                        try:
                            Info = self.parse_detail_page(source)
                        except:
                            pass
                        Info['网站'] = self.driver.current_url
                        print(Info)

                        # 保存入json文件
                        self.save_json(Info)

                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[1])  # 跳回列表页
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])  #跳回到首页

if __name__ == '__main__':
    fang_zf = Fang_zf()
    fang_zf.run()