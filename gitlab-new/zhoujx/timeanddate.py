# coding=utf-8 

'''
Author: 周俊贤
Email：673760239@qq.com

date:2019/7/23 14:30
'''

from selenium import webdriver
from lxml import etree
import time
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from lxml import etree
import requests
from lxml import etree
import pandas as pd
import datetime
from  auto_email import mail

# 得到网站的city列表citys
def get_city():
    response = requests.get('https://www.timeanddate.com/weather/china')
    html = etree.HTML(response.text)
    container = html.xpath("//a[contains(@href,'/weather/china')]")
    citys = []
    for each in container:
        city = each.xpath("./text()")[0]
        citys.append(city)
    return citys


citys = get_city()


class Timeanddate(object):
    driver_path = r'D:\chromedriver.exe'
    data = []

    def __init__(self, city, month, year):
        ################无头#######################################################3
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        self.driver = webdriver.Chrome('/usr/bin/chromedriver', options=chrome_options)
        # self.driver = webdriver.Chrome(executable_path=Timeanddate.driver_path)  #打开浏览器来启动
        #############################################################################
        #         self.driver.set_page_load_timeout(10)  # 设置页面最大加载时间

        self.city = city
        self.month = month
        self.year = year
        self.url = 'https://www.timeanddate.com/weather/china/{}/historic?month={}&year={}'.format(self.city,
                                                                                                   self.month,
                                                                                                   self.year)

    def run(self):
        # 防止读取页面时间过慢
        try:
            self.driver.get(self.url)
        except TimeoutException:
            print(u"加载超过10秒，强制停止加载。。。")
            self.driver.execute_script("window.stop()")
        #         #######################
        time.sleep(2)
        #         #######################

        source = self.driver.page_source
        month = self.get_days_eachmonth(source)  # 获取当月所有天数

        print(u"当月一共有多少{}天".format(month))

        selectTag = Select(self.driver.find_element_by_id('wt-his-select'))

        # 获取该月所有天
        for index in range(month):
            self.index = index
            selectTag.select_by_index(self.index)
            source = self.driver.page_source
            self.parse_page(source)  # 解析页面获取数据
        self.driver.close()

    # 得到每个月包含的天数
    def get_days_eachmonth(self, source):
        html = etree.HTML(source)
        days_eachmonth = html.xpath("//select[@id='wt-his-select']/option")
        # days_eachmonth = html.xpath("//div[@class='weatherLinks']//a")

        days_eachmonth = len(days_eachmonth)
        return days_eachmonth

    def parse_page(self, source):  # 获取当页的数据
        html = etree.HTML(source)
        hours = html.xpath("//table[@id='wt-his']/tbody/tr")
        for hour in hours:
            time = hour.xpath("./th/text()")
            content = hour.xpath("./td/text()")
            Temp = content[0]
            Temp = re.search('\d+', Temp).group()
            Weather = content[1]
            Weather = re.sub('\.', '', Weather)
            Comfort = content[2]
            Humidity = content[3]
            Barometer = content[4]
            Visibility = content[5]
            days = {
                'city': self.city,
                'year': self.year,
                'month': self.month,
                'day': self.index,
                'time': time,
                'Temp': Temp,
                'Weather': Weather,
                'Comfort': Comfort,
                'Humidity': Humidity,
                'Barometer': Barometer,
                'Visibility': Visibility
            }
            self.data.append(days)


#             print(self.index, days)

if __name__ == '__main__':
    data = []




import datetime

nowTime = datetime.datetime.now().strftime('%Y%m%d_%H%M')  # 现在


try:
    ssss
    for city in ['foshan']:
        print(city)
        for year in [2018]:
            print(year)
            for month in range(1, 13):
                print(u"开始爬{}月".format(month))
                spider = Timeanddate(city=city, month=month, year=year)
                spider.run()
                data.extend(spider.data)

except:
    mail_msg = "{}爬取timeanddate天气程序失败".format(nowTime)
    mail(my_sender='673760239@qq.com', my_pass='qnoaaoregjwjbbhi', to_user='673760239@qq.com',
         my_nick='周俊贤', to_nick='周俊贤', mail_msg=mail_msg)

data = pd.DataFrame.from_dict(data)

data.to_csv("{}.csv".format(nowTime), index=False)
