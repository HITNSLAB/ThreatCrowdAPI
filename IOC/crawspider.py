#!/usr/bin/python
# coding:utf-8
from __future__ import print_function, unicode_literals

import json
import threading
from queue import Queue

import requests
from bs4 import BeautifulSoup

from config import *
from logger_router import LoggerRouter
from proxy import get_ip_from_redis
from store import Store, SendBackProxy

logger = LoggerRouter().getLogger(__name__)

queue_ip = Queue()  # 任务队列，每一项为待探测的ip
mutex_href_get = threading.Lock()
mutex_href_put = threading.Lock()
sendbackproxy_object = SendBackProxy()  # 回收代理IP
threading.stack_size(65536)


def get_all(ip_string):
    """
    @ date: 2017-12-2
    @ author: wxw
    @ function: 接口函数，产生num个线程，在队列中取出IP进行爬取
    @ input: C段地址 如：182.40.12
    @ output: 完成标志 0 (int)
    """

    global queue_ip, mutex_href_get, mutex_href_put
    threads = []
    # 线程数量
    num = THREAD_NUM

    class_ip = ip_string
    proxies = {
        "http": get_ip_from_redis()
    }
    logger.info("正在获取C段地址 %s 中存在的IP列表" % class_ip)

    result = get_ip_list_from_class(class_ip, proxies)

    if isinstance(result, list):
        # 避免创建线程时白白消耗num个代理IP
        if result == []:
            logger.error("C段地址 %s 未发现IP列表" % class_ip)
            return 0

        for ip in result:
            queue_ip.put(ip)
        logger.info("C段地址 %s 中存在的IP列表获取完成" % class_ip)

        for i in range(0, num):
            threads.append(LookUp())

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    elif result == -2:
        Store().log_error_into_redis(class_ip)
    else:
        logger.error("C段地址 %s 未发现IP列表" % class_ip)

    return 0


def get_ip_list_from_class(class_ip, proxies):
    """
    在class_ip页面中获取该C段存在信息的ip
    :param class_ip: C段ip 如: 182.40.12
    :param proxies: 代理
    :return:
            =================== =========================
            值                  说明
            =================== =========================
            exist_ip_list(list) ip_list存在时的结果列表
            -1                  ip_list不存在
            -2                  超过最大重试次数，未成功获取
            =================== =========================
    """
    from requests.adapters import HTTPAdapter
    client = requests.Session()
    client.mount('http://', HTTPAdapter(max_retries=3))
    client.mount('https://', HTTPAdapter(max_retries=3))

    exist_ip_list = []
    proxies = proxies

    retry_count = RETRY_COUNT
    while retry_count != 0:
        try:
            class_content = client.get("https://www.threatcrowd.org/listIPs.php?class=" + class_ip,
                                       timeout=4, proxies=proxies if PROXY_ENABLED else []).content
            break
        except Exception as e:
            logger.info("代理出现错误，retrying to get %s" % class_ip)
            logger.info(e)
            retry_count -= 1
            proxies = {
                "http": get_ip_from_redis()
            }
            if retry_count == 0:
                return -2
            continue
    try:
        ip_table = BeautifulSoup(class_content, "lxml").find(attrs={"class": "table table-striped"})
        for item in ip_table:
            try:
                ip = item.find("td").find("a").get_text()
                # 检测是否是属于该段的IP
                if str(ip).split(".")[2] == class_ip.split(".")[2]:
                    # class_content页面中，最后一行的IP后有换行符
                    ip = ip.replace("\r", "")
                    exist_ip_list.append(ip)
                else:
                    logger.info("the ip %s does not belong to %s" % (ip, class_ip))
            except Exception as e:
                # 可能获取到空段，舍去
                pass
    except TypeError as e:
        logger.info(e)
        logger.info("极特殊情况，获取到的页面是空")
        return -1

    sendbackproxy_object.send_back_proxy_into_redis(proxies["http"])

    if exist_ip_list is None:
        logger.info("未发现")
        return -1
    else:
        for ip in exist_ip_list:
            logger.info(ip)
        return exist_ip_list


class LookUp(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.store_object = Store()

    def run(self):
        """
        在队列中获取由C段IP得到的要爬取的IP，并调用Parser，结果/状态入库
        注： 由于要求，没有md5_list的情况由错误状态1 已经改为了 正确结果，只不过结果中的md5为[]
        """
        global queue_ip, mutex_href_get, mutex_href_put
        mutex_href_get.acquire()

        proxies = {
            "http": get_ip_from_redis()
        }

        while queue_ip.qsize() > 0:
            # 在线程池中取得链接和序号
            view_href = SPIDER_URL + queue_ip.get()

            mutex_href_get.release()

            # 调用Parser实际爬取
            parser_object = Parser(view_href, proxies)
            result = parser_object.detect_ip()

            try:
                mutex_href_put.acquire()
                if result != -1 and result != -2:
                    logger.info(view_href.split(".")[-1])
                    logger.info("--------------------------")
                    self.store_object.store_into_redis(result)
                    logger.info("存储成功")
                    logger.info("--------------------------")
                elif result == -1:
                    logger.info("当前ip没有此类信息，记录空----%s" % view_href)
                    result = {
                        "ip": str(view_href).split("ip=")[1],
                        "md5": []
                    }
                    self.store_object.store_into_redis(result)
                    # self.store_object.log_error_into_redis(view_href, status="-1")
                else:
                    self.store_object.log_error_into_redis(view_href, status="-2")
                    logger.info("重试已达最大次数，失败 %s" % view_href)
                mutex_href_put.release()
            except Exception as e:
                mutex_href_put.release()
                mutex_href_get.acquire()
                self.store_object.log_error_into_redis(view_href, status="-3")
                logger.info(e)
                continue
            mutex_href_get.acquire()
        mutex_href_get.release()


class Parser(object):
    """
    实际爬取并解析网页的类
    """

    def __init__(self, ip_href, initial_proxies):
        """
        :param ip_href: 任务，格式为 SPIDER_URL + IP
        :param initial_proxies: 初始的代理
        """
        self.ip_href = ip_href
        self.proxies = initial_proxies
        self._md5_list = []
        self.info_dict = {}

        from requests.adapters import HTTPAdapter

        self.client = requests.Session()
        self.client.mount('http://', HTTPAdapter(max_retries=3))
        self.client.mount('https://', HTTPAdapter(max_retries=3))

    def detect_ip(self):
        """
        探测任务链接是否存在md5， 若有则调用detect_md5
        :return:
                =============== =========================
                值              说明
                =============== =========================
                info_dict(dict) md5_list存在时的结果字典
                -1              md5_list不存在
                -2              超过最大重试次数，未成功获取
                =============== =========================
        """
        retry_count = RETRY_COUNT
        while retry_count != 0:
            try:
                content = self.client.get(self.ip_href, timeout=5, proxies=self.proxies,
                                          headers=headers).content
                logger.info("Got '%s' ip successfully!" % self.ip_href)

                ip_dict = json.loads(content)
                logger.info('Got ip_dict = %s' % ip_dict)

                if ip_dict["response_code"] == "1":
                    logger.info("Status code of ip_href '%s' is 1 " % self.ip_href)
                    self.info_dict["ip"] = self.ip_href.split("=")[-1]
                    self.info_dict["md5"] = []
                    logger.info("MD5如下：%s" % ip_dict["hashes"])
                    if ip_dict["hashes"]:

                        self._md5_list = ip_dict["hashes"]
                        if self.detect_md5() == -2:
                            return -2
                    else:
                        logger.warning("未发现md5。。。")
                        return -1
                else:
                    return -1

                logger.info("----------------")
                return self.info_dict

            except Exception as e:
                logger.error("ip_href '%s', exception '%s'代理出现错误，正在重试..." % (self.ip_href, e))

                retry_count -= 1
                self.proxies = {
                    "http": get_ip_from_redis()
                }

        return -2

    def detect_md5(self):
        """
        探测md5_list中每一项md5对应的信息
        :return:
                =============== =========================
                值              说明
                =============== =========================
                None(None)      md5_list探测成功
                -2              超过最大重试次数，未成功获取
                =============== =========================
        """

        expected_flag = False

        logger.info('MD5 list = %s' % self._md5_list)

        for md5 in self._md5_list:
            if md5 == '':
                continue
            else:
                logger.info(md5)
            retry_count = RETRY_COUNT
            while retry_count != 0:
                try:
                    # time.sleep(2)
                    expected_flag = False

                    md5_href = MD5_URL + str(md5)
                    content = self.client.get(md5_href, timeout=5, proxies=self.proxies, headers=headers).content

                    temp_md5_dict = json.loads(content)
                    if str(temp_md5_dict["response_code"]) == "0":
                        logger.warning("可能是陷阱， 未发现MD5 '%s' of '%s'" % (md5_href, self.ip_href))
                        break
                    info_md5_dict = {
                        md5: {
                            "sha1": temp_md5_dict["sha1"],
                            "domains": temp_md5_dict["domains"]
                        }
                    }

                    self.info_dict["md5"].append(info_md5_dict)
                    logger.info("Got MD5 '%s' of %s successfully!" % (str(md5), self.ip_href))
                    break
                except Exception as e:
                    expected_flag = True
                    logger.error("MD5 '%s', ip_href '%s', 代理出现错误，正在重试..." % (md5, self.ip_href))
                    logger.info(e)
                    retry_count -= 1
                    self.proxies = {
                        "http": get_ip_from_redis()
                    }

        if expected_flag:
            return -2

        sendbackproxy_object.send_back_proxy_into_redis(self.proxies["http"])

        return None


if __name__ == '__main__':
    get_all("188.40.3")
