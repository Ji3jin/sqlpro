#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : redisobj.py
# Author: jixin
# Date  : 18-10-25
import redis
import os
from config import config


class RedisInstance(object):
    def __init__(self):
        config_name = os.getenv('FLASK_CONFIG') or 'default'
        redis_host = config[config_name].REDIS_HOST
        redis_port = config[config_name].REDIS_PORT
        self.pool = redis.ConnectionPool(host=redis_host, port=redis_port, decode_responses=True)

    def get_instance(self):
        return redis.Redis(connection_pool=self.pool)

redis_pool = RedisInstance()