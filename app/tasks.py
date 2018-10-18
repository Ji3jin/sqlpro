#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : tasks.py
# Author: jixin
# Date  : 18-10-18
from . import celery
from flask import current_app


@celery.task
def apptask():
    print(current_app.name)

# start sqoop task by db