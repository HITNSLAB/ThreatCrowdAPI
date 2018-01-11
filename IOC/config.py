#!/usr/bin/python
# coding:utf-8
from __future__ import unicode_literals

# ================================================================================
# get_task.py

# 获取任务的API
TASK_API = "http://172.26.253.78/ip_queue/ip_start.php?queue=find"
# 任务完成状态的API
RESULT_API = "http://172.26.253.78/ip_queue/ip_finished.php?finished="

# ================================================================================
# crawspider.py

# 代理IP Redis数据库的主机地址
REDIS_PROXY_HOST = "172.29.152.141"
# Redis中代理IP所在list的名称
REDIS_PROXY_LISTNAME = "ip_list"
# 目的API_1的前缀
SPIDER_URL = "https://www.threatcrowd.org/searchApi/v2/ip/report/?ip="
# 目的API_2的前缀
MD5_URL = "https://www.threatcrowd.org/searchApi/v2/file/report/?resource="
# 一次性获取的IP代理的个数
TEST_IP_LIST_COUNT = 1
# 爬取线程数
THREAD_NUM = 4
# 检测代理IP是否可用的网址
TEST_URL = "https://www.threatcrowd.org/searchApi/v2/ip/report/?ip=0.0.0.0"
# 失败重试次数
RETRY_COUNT = 10

# ================================================================================
# store.py

# 存储结果/错误信息所在Redis数据库的主机地址（中转）
REDIS_RESULT_HOST = "172.29.152.200"
# 存储错误信息所在Redis数据库的表名（中转）
REDIS_ERROR_TABLE = "error"
# 存储结果所在Redis数据库的表名（中转）
REDIS_RESULT_TABLE = "result"
# 存储缺少代理警告信息所在Redis数据库的表名（中转）
REDIS_LACK_TABLE = "lack"

# ================================================================================
# transfer.py

# 存储结果/错误信息所在Mongo数据库的主机地址（总）
MONGO_RESULT_HOST = [
            '172.29.152.200',
            '172.29.152.141',
            '172.29.152.142',
            '172.29.152.143',
            '172.29.152.144',
            '172.29.152.145',
            '172.29.152.146',
            '172.26.253.147'
        ]
MONGO_RESULT_DB = "threatcrowd"
MONGO_RESULT_CL = "result"
MONGO_ERROR_CL = "error"
MONGO_LACK_CL = "lack"

# 用户
MONGO_USER = "manager-rw"
MONGO_PASSWORD = "HITdbManager-rw!"

# 转存间隔时间
TRANSFER_TIME = 200

# ================================================================================

# # 代理IP获取的网址
# ZHANDAYE_URL = "http://api.zdaye.com/?api=201711281044061107&checktime=2&rtype=1&ct="

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, sdch',
    'accept-language': 'zh-CN,zh;q=0.8',
    'cache-control': 'max-age=0',
    'cookie': '__cfduid=d8945ed8605813e4506aafa55d5601fb31512649278',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36',
    'connection': 'close'
}

ISOTIMEFORMAT = "%Y-%m-%d %X"
