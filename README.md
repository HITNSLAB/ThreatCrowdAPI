ThreatCrowdAPI
=========================================
```
.
├── README.md             
├── LICENSE                 
├── IOC                     # Main project folder
│   ├── config.py           # config module containing general constant
│   ├── crawspider.py       # Task Center module (main entrance and logic control)
│   ├── get_task.py         # Entry module
│   ├── proxy.py            # Proxy module to get proxy_ip
│   ├── store.py            # Redis database module
│   ├── test.py             # Test cases
│   └── transfer.py         # Transfer module
└── ...
```
## NOTE: 对于不同docker所在的不同虚拟机，修改config.py的中转Redis地址字段

# 使用方式
``` python get_task.py```

# 简单流程
* 入口文件为get_task.py，当运行时，会从任务队列API中获取C段IP，传入crawspider.py中进行处理。

* crawspider.py接收一个C段IP任务。\
由于爬取需要代理，因此调用proxy.py中的get_ip_from_redis函数获取验证可用的代理IP，然后请求并解析网页A，网页A存在该C段IP中拥有IOC信息的IP列表。将这些IP抽取出来存入Queue队列，然后开启num个线程，对队列中的IP对应的API进行探测。

* 探测结果存入中转的Redis数据库。可能有4种状态。
    1) 该IP拥有所需的IOC信息，正常存入
    2) 该IP不拥有所需的IOC信息，正常存入，只不过对应的md5列表为[]
    3) 探测该IP时超过了最大重试次数，失败。返回-2，并存储相应错误信息
    4) 存入数据库时失败。返回-3，并存储相应错误信息

* 在调用proxy.py中的get_ip_from_redis函数时，有可能代理池中的代理已用完。在用完时，返回-4，存储相应信息。同时每隔30秒不断重试。
