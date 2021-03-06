#!/usr/bin/python
# coding:utf-8
from __future__ import print_function, unicode_literals

# import requests
from requests.adapters import HTTPAdapter

import crawspider
from config import *
from logger_router import LoggerRouter

logger = LoggerRouter().getLogger(__name__)
import cfscrape


def main():
    """
    项目入口
    """

    logger.info("已启动。。")

    # request_client = requests.Session()
    request_client = cfscrape.create_scraper()
    request_client.mount('http://', HTTPAdapter(max_retries=3))

    while True:
        try:
            task_content = request_client.get(TASK_API).content
            logger.info(task_content)
        except Exception as e:
            logger.error("任务队列服务器崩溃, exception: '%s'" % e)
            break

        info_dict = eval(str(task_content).split("y")[1].split("<")[0])
        logger.info(info_dict["id"])
        ip_group_list = info_dict["ip"].split(".")
        info_dict["ip"] = ip_group_list[0] + "." + ip_group_list[1] + "." + ip_group_list[2]
        logger.info(info_dict["ip"])

        crawspider.get_all(info_dict["ip"])

        result_content = request_client.get(RESULT_API + info_dict["id"]).content
        logger.info(result_content)

    logger.info("所有任务均爬取完成，请核对数据库中可能存在的因中断而极个别漏爬的IP")


if __name__ == '__main__':
    main()
