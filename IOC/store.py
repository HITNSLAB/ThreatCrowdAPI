#!/usr/bin/python
# coding:utf-8
from __future__ import print_function, unicode_literals

import socket
import time

import redis

from config import *


class Store(object):

    def __init__(self):
        """
        将结果存储至中转Redis服务器
        """
        self.redis_client = redis.Redis(host=REDIS_RESULT_HOST)

    def store_into_redis(self, info_dict):
        """
        注： 当目的IP不存在对应md5，即log_error_into_redis函数返回-1时，也记录，只不过结果对应项为空
        """
        self.redis_client.lpush(REDIS_RESULT_TABLE, str(info_dict))

    def log_error_into_redis(self, ip, status="-2"):
        """
        :param ip: 出错时的目标IP
        :param status: 状态值
                =============== =========================
                值              说明
                =============== =========================
                -1              目的IP不存在对应md5  （已作废）
                -2              超过最大重试次数，未成功获取
                -3              意外，连接数据库存储时失败
                =============== =========================
        :return: None (None)
        """
        now_datetime = time.strftime(ISOTIMEFORMAT, time.localtime(time.time()))
        error_dict = {
            "status": status,
            "ip": ip,
            "datetime": now_datetime
        }
        self.redis_client.lpush(REDIS_ERROR_TABLE, str(error_dict))

    def log_lack_proxy_into_redis(self, status="-4"):
        """
        将缺少代理的情况存储至中转Redis
        """
        now_datetime = time.strftime(ISOTIMEFORMAT, time.localtime(time.time()))
        name = socket.getfqdn(socket.gethostname())
        addr = socket.gethostbyname(name)
        error_dict = {
            "status": status,
            "ip": addr,
            "datetime": now_datetime
        }
        self.redis_client.lpush(REDIS_ERROR_TABLE, str(error_dict))


class SendBackProxy(object):
    """
    在爬取每个任务结束后，归还该任务的代理IP，节约代理资源
    """
    def __init__(self):
        self.redis_client = redis.Redis(host=REDIS_PROXY_HOST)

    def send_back_proxy_into_redis(self, ip):
        self.redis_client.rpush(REDIS_ERROR_TABLE, ip)
        # print("已归还", ip)
