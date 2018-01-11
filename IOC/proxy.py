#!/usr/bin/python
# coding:utf-8
from __future__ import unicode_literals

import json
import time

import redis
import requests

from config import *
from logger_router import LoggerRouter
from store import Store

logger = LoggerRouter().getLogger(__name__)

log_object = Store()


def get_ip_from_redis():
    """
    在代理池中获取代理IP并检验是否可用
    :return: 可用的代理IP字符串，如"1.1.1.1"
    """
    redis_client = redis.Redis(host=REDIS_PROXY_HOST)

    while True:
        ip_list = []
        for i in range(TEST_IP_LIST_COUNT):
            ip = redis_client.rpop(REDIS_PROXY_LISTNAME)
            ip_list.append(ip)

        # 检查是否都为None
        if ip_list[-1] is None:
            logger.info("代理ip 已用完，正在等待重试。。")
            time.sleep(30)
            # 记录代理IP用完时导致不断重试的时间
            log_object.log_lack_proxy_into_redis()
            continue

        useful_ip = test_useful_ip(ip_list)

        if useful_ip:
            return useful_ip


def test_useful_ip(ip_list):
    """
    检测代理IP是否可用
    """
    for ip in ip_list:
        try:
            test_proxies = {
                "http": ip,
            }
            test_content = requests.get(TEST_URL, timeout=5, proxies=test_proxies, headers=headers).content
        except Exception as e:
            logger.info(e)
            continue
        test_dict = json.loads(test_content)
        try:
            if test_dict["response_code"] == "1":
                logger.info("the ip %s is useful !" % ip)
                return ip
        except Exception as e:
            logger.info(e)
            continue

    return None
