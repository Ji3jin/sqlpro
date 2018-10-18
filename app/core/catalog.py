#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : catalog.py
# Author: jixin
# Date  : 18-10-18

from enum import Enum


class CataLog(Enum):
    HIVE = 'hive'
    MYSQL = 'mysql'
    JMX = 'jmx'
    POSTGRESQL = 'postgresql'
    MONGO = 'mongo'

    @classmethod
    def choices(cls):
        return [(choice, choice.name) for choice in cls]

    @classmethod
    def coerce(cls, item):
        return cls(item) if not isinstance(item, cls) else item

    def __str__(self):
        return str(self.value)