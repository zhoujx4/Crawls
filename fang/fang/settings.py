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
DOWNLOAD_DELAY = 0.5
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

cookielist = "global_cookie=k01uwmjz0b3uq1vxzcu0sdnp120k0qugsfp; new_search_uid=cb558123895eef60fd8ce6e0516fa59e; newhouse_user_guid=C2400E4A-AE2B-CFEC-79DA-5C7E201F2FCC; vh_newhouse=1_1568907351_458%5B%3A%7C%40%7C%3A%5Da832c653db46694801e4f390b19d98d2; integratecover=1; __utma=147393320.606298494.1568906577.1569814740.1570677285.4; __utmc=147393320; __utmz=147393320.1570677285.4.4.utmcsr=gz.fang.com|utmccn=(referral)|utmcmd=referral|utmcct=/; ASP.NET_SessionId=xzo54wvu4w11nm2ldekgz1v2; city=cs; Rent_StatLog=bbfcfc5c-502d-4381-b777-ed414959b367; keyWord_recenthousecs=%5b%7b%22name%22%3a%22%e4%b8%9c%e6%96%b9%e6%96%b0%e5%9f%8e%22%2c%22detailName%22%3a%22%22%2c%22url%22%3a%22%2fhouse%2fs31-kw%25b5%25d8%25cc%25fa%25bf%25da%25b6%25ab%25b7%25bd%25d0%25c2%25b3%25c7%25d0%25c2%25ca%25c0%25bc%25cd%25bc%25d2%25d4%25b0%25b3%25a4%25d4%25b6%25be%25ab%25d7%25b0%25d0%25de%25c8%25fd%25b7%25bf%25b3%25cf%25d0%25c4%25b3%25f6%25d7%25e2%252c%25bd%25bb%25cd%25a8%25b1%25e3%25c0%25fb%2f%22%2c%22sort%22%3a3%7d%5d; __utmt_t0=1; __utmt_t1=1; __utmt_t2=1; g_sourcepage=zf_fy%5Elb_pc; Captcha=7A4747786D6362422B2F475A35526F576D786153703251702F32494B314E2F344875645A326A737475756B5A6F73647736426736547975787467782B6D4B733336325570325672616730413D; unique_cookie=U_tgkz8n6dowcs45ucg90lfa1ak1sk1k4p28a*12; __utmb=147393320.33.10.1570677285"
# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
  'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
  'accept-encoding': 'gzip, deflate, br',
  'accept-language': 'zh-CN,zh;q=0.9',
  'referer' : 'https://cs.zu.fang.com/',
  'sec-fetch-mode' : 'navigate',
  'sec-fetch-site' : 'same-origin',
  'sec-fetch-user' : '?1',
  'upgrade-insecure-requests' : '1',
  'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
  "Cookie" : cookielist
}
# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'fang.middlewares.FangSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'fang.middlewares.ProxyMiddleware': 543,
# }

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