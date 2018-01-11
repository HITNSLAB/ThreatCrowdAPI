FROM python

MAINTAINER WANG XIAOWEI & LI YANZHE

WORKDIR /usr/src/app

ADD ./IOC ./IOC

RUN apt -y update \
    && apt -y upgrade \
    && pip2 install scrapy_redis bs4 pymongo \
    && apt -y install tor proxychains

WORKDIR slaveNode/slaveNode