#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : views.py
# Author: jixin
# Date  : 18-10-17

from app import db
from . import etl
from ..core import baseapi
from ..tasks import *


@etl.route('/etl/task', methods=['POST'])
def tasktest():
    r = apptask.delay()
    return baseapi.success("ok")
