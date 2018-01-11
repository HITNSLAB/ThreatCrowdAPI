#!/usr/bin/python
# coding:utf-8
from __future__ import print_function, unicode_literals

import requests
from requests.adapters import HTTPAdapter

import crawspider
from config import *


def main():
    """
    项目入口
    """

    print("已启动。。")

    request_client = requests.Session()
    request_client.mount('http://', HTTPAdapter(max_retries=3))

    while True:
        try:
            task_content = request_client.get(TASK_API).content
        except Exception as e:
            print(e)
            print("任务队列服务器崩溃")
            break

        info_dict = eval(str(task_content).split("y")[1].split("<")[0])
        print(info_dict["id"])
        ip_group_list = info_dict["ip"].split(".")
        info_dict["ip"] = ip_group_list[0] + "." + ip_group_list[1] + "." + ip_group_list[2]
        print(info_dict["ip"])

        crawspider.get_all(info_dict["ip"])

        result_content = request_client.get(RESULT_API + info_dict["id"]).content
        print(result_content)

    print("所有任务均爬取完成，请核对数据库中可能存在的因中断而极个别漏爬的IP")


def test():
    crawspider.get_all("54.68.226")

if __name__ == '__main__':
    test()
