# -*- coding: utf-8 -*-

# Scrapy settings for fang project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'fang'

SPIDER_MODULES = ['fang.spiders']
NEWSPIDER_MODULE = 'fang.spiders'

# LOG_LEVEL = 'INFO'
LOG_STDOUT = False

CONCURRENT_REQUESTS = 1



# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'fang (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False



# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 2
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# cookielist = "global_cookie=kfonpu3mxupvcizlhufc9jnxw18jz2n1e9h; Integrateactivity=notincludemc; budgetLayer=1%7Cbj%7C2019-08-08%2020%3A08%3A56; lastscanpage=0; resourceDetail=1; integratecover=1; new_search_uid=105c7db9fc0c3db277418a0bde18e35a; newhouse_user_guid=366E737D-3DD4-39B3-DD83-B17703D18F2C; vh_newhouse=1_1565408395_216%5B%3A%7C%40%7C%3A%5Dab5f7409ed66bc38e69ab666fd75899b; keyWord_recenthousegz=%5b%7b%22name%22%3a%22%e5%a2%9e%e5%9f%8e%22%2c%22detailName%22%3a%22%22%2c%22url%22%3a%22%2fhouse-a080%2f%22%2c%22sort%22%3a1%7d%2c%7b%22name%22%3a%22%e5%a4%a9%e6%b2%b3%22%2c%22detailName%22%3a%22%22%2c%22url%22%3a%22%2fhouse-a073%2fg22%2f%22%2c%22sort%22%3a1%7d%2c%7b%22name%22%3a%22%e6%b5%b7%e7%8f%a0%22%2c%22detailName%22%3a%22%22%2c%22url%22%3a%22%2fhouse-a074%2fg21-i310%2f%22%2c%22sort%22%3a1%7d%5d; keyWord_recenthousesz=%5b%7b%22name%22%3a%22%e6%b7%b1%e5%9c%b3%e5%91%a8%e8%be%b9%22%2c%22detailName%22%3a%22%22%2c%22url%22%3a%22%2fhouse-a016375%2f%22%2c%22sort%22%3a1%7d%2c%7b%22name%22%3a%22%e4%b8%9c%e8%8e%9e%22%2c%22detailName%22%3a%22%22%2c%22url%22%3a%22%2fhouse-a013057%2f%22%2c%22sort%22%3a1%7d%2c%7b%22name%22%3a%22%e6%83%a0%e5%b7%9e%22%2c%22detailName%22%3a%22%22%2c%22url%22%3a%22%2fhouse-a013058%2f%22%2c%22sort%22%3a1%7d%5d; keyWord_recenthousedg=%5b%7b%22name%22%3a%22%e9%81%93%e6%bb%98%22%2c%22detailName%22%3a%22%22%2c%22url%22%3a%22%2fhouse-a0800%2f%22%2c%22sort%22%3a1%7d%2c%7b%22name%22%3a%22%e6%9d%be%e5%b1%b1%e6%b9%96%22%2c%22detailName%22%3a%22%22%2c%22url%22%3a%22%2fhouse-a0927%2f%22%2c%22sort%22%3a1%7d%2c%7b%22name%22%3a%22%e4%b8%9c%e8%8e%9e%e5%91%a8%e8%be%b9%22%2c%22detailName%22%3a%22%22%2c%22url%22%3a%22%2fhouse-a013485%2f%22%2c%22sort%22%3a1%7d%5d; __utmz=147393320.1565585248.17.12.utmcsr=search.fang.com|utmccn=(referral)|utmcmd=referral|utmcct=/captcha-verify/redirect; g_sourcepage=ehlist; city=jx; __utma=147393320.36125272.1565266133.1565700590.1565742487.22; __utmc=147393320; __utmt_t0=1; __utmt_t1=1; __utmt_t2=1; __utmb=147393320.3.10.1565742487; unique_cookie=U_57ovli9q7xduu4gyq3hh2uh8o17jzaindc4*1"
# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
  'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
  'accept-encoding' : 'gzip, deflate, br',
  'accept-language' : 'zh-CN,zh;q=0.9',
  'referer' : 'https://jx.esf.fang.com/',
  # 'cache-control' : 'max-age=0',
  # 'sec-fetch-mode' : 'navigate',
  # 'sec-fetch-site' : 'none',
  # 'sec-fetch-user' : '?1',
  # 'upgrade-insecure-requests' : '1',
  'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1',
  # "Cookie" : cookielist
}
# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'fang.middlewares.FangSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   'fang.middlewares.ProxyMiddleware': 543,
}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    'fang.pipelines.FangPipeline': 300,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# REDIRECT_ENABLED = False                       # 关掉重定向, 不会重定向到新的地址
# HTTPERROR_ALLOWED_CODES = [301, 302]     # 返回301, 302时, 按正常返回对待, 可以正常写入cookie