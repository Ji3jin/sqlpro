#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : baseview.py
# Author: jixin
# Date  : 18-10-18
import time
from functools import wraps


def fn_timer(function):
    """
     prints costs time for every function
    :param function:
    :return:
    """

    @wraps(function)
    def function_timer(*args, **kwargs):
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        print("Total time running %s: %s seconds" % (function.func_name, str(t1 - t0)))
        return result

    return function_timer
