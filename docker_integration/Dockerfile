FROM python

MAINTAINER WANG XIAOWEI & LI YANZHE

WORKDIR /usr/src/app

ADD ./IOC ./IOC

WORKDIR IOC

RUN apt -y update \
    && apt -y upgrade \
    && apt -y install proxychains

RUN pip install -r requirements.txt

ADD ./proxychains.conf /etc/proxychains.conf
