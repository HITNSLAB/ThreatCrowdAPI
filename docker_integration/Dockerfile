FROM python

MAINTAINER WANG XIAOWEI & LI YANZHE

WORKDIR /usr/src/app

ADD ./IOC ./IOC

WORKDIR IOC

RUN pip install -r requirements.txt

RUN apt -y install proxychains

ADD ./proxychains.conf /etc/proxychains.conf
