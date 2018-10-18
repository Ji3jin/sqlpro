#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : baseapi.py
# Author: jixin
# Date  : 18-10-18
import functools
from flask import jsonify, current_app
import json
import logging


def success(data, status_code=200, **kwargs):
    result = {
        'status': 'success',
        'data': data,
    }
    resp = {**result, **kwargs}
    return jsonify(resp), status_code


def failed(err_msg, status_code=200, **kwargs):
    result = {
        'status': 'failed',
        'error': err_msg,
    }
    resp = {**result, **kwargs}
    return jsonify(resp), status_code


def catch(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return exception(e)

    return inner


def exception(e):
    current_app.logger.error("error " + e)
    resp = {
        'status': 500,
        'message': 'Unknown exception.',
        'data': e
    }
    return jsonify(resp), 500
