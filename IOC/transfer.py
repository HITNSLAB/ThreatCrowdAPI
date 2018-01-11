#!/usr/bin/python
# coding:utf-8
from __future__ import print_function, unicode_literals

import time
from urllib.parse import quote_plus

import redis
from pymongo import MongoClient

from config import *
from logger_router import LoggerRouter

logger = LoggerRouter().getLogger(__name__)


def monitor():
    monitor_redis_client = redis.Redis(host=REDIS_RESULT_HOST)

    uris = [
        "mongodb://%s:%s@%s" % (quote_plus(MONGO_USER), quote_plus(MONGO_PASSWORD), host) for host in MONGO_RESULT_HOST
    ]

    result_mongo_client = MongoClient(
        host=uris,
        replicaset=MONGO_REPLICASET,
        readPreference='secondary',
    )

    db = result_mongo_client[MONGO_RESULT_DB]
    result_collection = db[MONGO_RESULT_CL]
    error_collection = db[MONGO_ERROR_CL]
    lack_collection = db[MONGO_LACK_CL]

    while True:
        count = monitor_redis_client.llen(REDIS_RESULT_TABLE)
        while count != 0:
            result = monitor_redis_client.lpop(REDIS_RESULT_TABLE)
            logger.info(result)
            # 将中转Redis数据库中存储的字符串类型的结果转为字典
            result = eval(result)
            result_collection.insert(result)
            count -= 1

        count = monitor_redis_client.llen(REDIS_ERROR_TABLE)
        while count != 0:
            error_result = monitor_redis_client.lpop(REDIS_ERROR_TABLE)
            # 将中转Redis数据库中存储的字符串类型的结果转为字典
            logger.error(error_result)
            error_result = eval(error_result)
            error_collection.insert(error_result)
            count -= 1

        count = monitor_redis_client.llen(REDIS_LACK_TABLE)
        while count != 0:
            lack_result = monitor_redis_client.lpop(REDIS_LACK_TABLE)
            # 将中转Redis数据库中存储的字符串类型的结果转为字典
            logger.info(lack_result)
            lack_result = eval(lack_result)
            lack_collection.insert(lack_result)
            count -= 1

        time.sleep(TRANSFER_TIME)


if __name__ == '__main__':
    monitor()
