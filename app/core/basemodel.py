#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : basemodel.py
# Author: jixin
# Date  : 18-10-19
from enum import Enum


class Serializable(object):
    class FieldNotFound(Exception):
        pass

    def serialize(self, fields=[]):
        convert = dict()
        # add your coversions for things like datetime's
        # and what-not that aren't serializable.
        d = dict()
        for c in self.__class__.__table__.columns:
            v = getattr(self, c.name)
            if c.type in convert.keys() and v is not None:
                try:
                    d[c.name] = convert[c.type](v)
                except:
                    d[c.name] = "Error:  Failed to covert using ", str(convert[c.type])
            elif v is None:
                d[c.name] = str()
            elif isinstance(v, Enum):
                d[c.name] = v.value
            else:
                d[c.name] = v
        return d
