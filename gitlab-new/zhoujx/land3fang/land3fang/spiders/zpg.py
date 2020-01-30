# -*- coding: utf-8 -*-
import scrapy


class ZpgSpider(scrapy.Spider):
    name = 'zpg'
    allowed_domains = ['3fang.com']
    start_urls = ['http://3fang.com/']

    # def start_requests(self):
    #     url = "http://passport.3fang.com/loginsendmsm.api"
    #     data = {
    #             "MobilePhone" : "15625122214",
    #             "Operatetype" : "0",
    #             "Service" : "soufun-3fang-web"
    #             }
    #     request = scrapy.FormRequest(url, formdata=data, callback=self.log_in)
    #
    #     print('test')
    #     yield request


    def start_requests(self):
        url = "https://passport.fang.com/login.api"
        data = {
            "uid" : "15625122214",
            "pwd" : "321b98fc5ef89aad21f46d346174b2a225a3ba7c8cfd3a1c2db0e9ab9de9dd90fbf1be3af288c64cc6c653a6aea245be9d19e1414534b1df423c3a0eb673fa529c3fe542d61fdc2a0244340f504ab346b26592870402e4e8f51a6acd7389d1b6bad202ef05d1dcbb5416021487458d70e629e072c7b0522f25f31aa433487ac0",
            "Service" : "soufun-3fang-web",
            "AutoLogin" : "1"
                }
        request = scrapy.FormRequest(url, formdata=data, callback=self.parse_page)

        print('test')
        yield request


    # def log_in(self, response):
    #
    #     code = input('验证码是')
    #     url = "http://passport.3fang.com/loginverifysms.api?mobilephone=15625122214&mobilecode={}&operatetype=0&service=soufun-3fang-web".format(code)
    #
    #     request = scrapy.Request(url, callback=self.parse_page)
    #     yield request

    def parse_page(self, response):

        print('结束')
        pass
