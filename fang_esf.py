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

]


深圳 = [

        ]
东莞 = [

]  
    
    
'''

# 湖南
'''
"https://yueyang.esf.fang.com/",  #岳阳 28页
[
"https://zhuzhou.esf.fang.com/house/g21/" #株洲 一居 5页
"https://zhuzhou.esf.fang.com/house/g22/" #株洲 二居 18页
"https://zhuzhou.esf.fang.com/house/g23/" #株洲 三居 60页
"https://zhuzhou.esf.fang.com/house/g24/" #株洲 四居 21页
"https://zhuzhou.esf.fang.com/house/g25/" #株洲 五居 6页
"https://zhuzhou.esf.fang.com/house/g299/"#株洲 五居以上 4页
]
"https://shaoyang.esf.fang.com/",  #邵阳 14页
"https://loudi.esf.fang.com/",     #娄底 6页
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