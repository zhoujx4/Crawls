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

    def __init__(self, city, month, year):
        ################无头#######################################################3
        # chrome_options = Options()
        # chrome_options.add_argument('--headless')
        # self.driver = webdriver.Chrome('D:/chromedriver.exe', options=chrome_options)
        self.driver = webdriver.Chrome(executable_path=Timeanddate.driver_path)  #打开浏览器来启动
        #############################################################################
        self.driver.set_page_load_timeout(10)  # 设置页面最大加载时间
        self.data = []
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
            print("加载页面超时")
            self.driver.execute_script("window.stop()")
        #######################
        time.sleep(2)
        #######################

        source = self.driver.page_source
        month = self.get_days_eachmonth(source)  # 获取当月所有天数

        print(month)

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
        print(days_eachmonth)
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
            print(self.index, days)

if __name__ == '__main__':
    data = []

    for city in ['foshan']:
        print(city)
        for year in [2018]:
            print(year)
            for month in range(1, 2):
                spider = Timeanddate(city=city, month=month, year=year)
                spider.run()
                data.extend(spider.data)

