from logging.handlers import *
from queue import Queue
import sys


class Singleton(type):
    _instances = {}

    def __call__(self, *args, **kwargs):
        if self not in self._instances:
            self._instances[self] = super(Singleton, self).__call__(*args, **kwargs)
        return self._instances[self]


class LoggerRouter(metaclass=Singleton):
    def __init__(self, listener_no=4):
        self.level = None
        self.formatter = None
        self.handlers = []
        self.initialize_default_config()
        self.queue = Queue(100)
        self.que_handler = self._config_handler(QueueHandler(self.queue))
        self.listeners = [QueueListener(self.queue, *self.handlers) for i in range(listener_no)]
        for ls in self.listeners:
            ls.start()

    def getLogger(self, name=None):
        return self._config_logger(logging.getLogger(name))

    def _config_handler(self, hd, fmt=None, lvl=None):
        fmt = fmt if fmt else self.formatter
        lvl = lvl if lvl else self.level
        hd.setLevel(lvl)
        hd.setFormatter(fmt)
        return hd

    def _config_logger(self, logger):
        logger.addHandler(self.que_handler)
        logger.setLevel(self.level)
        return logger

    def initialize_default_config(self):
        self.level = logging.INFO
        self.formatter = logging.Formatter('%(asctime)s %(levelname)-8s [%(name)s:%(lineno)s] %(message)s',
                                           datefmt='%Y-%m-%d %H:%M:%S')
        self.handlers = [
            # logging.NullHandler(),
            self._config_handler(
                logging.StreamHandler(sys.stdout),
            ),
        ]
