#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : models.py
# Author: jixin
# Date  : 18-10-19
from datetime import datetime
from .. import db
from ..core.basemodel import Serializable


class TaskInfo(db.Model, Serializable):
    __tablename__ = 't_task_info'
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(64),
                          nullable=False, unique=True, index=True)
    sqoop_param = db.Column(db.String(64), nullable=False)
    is_scheduled = db.Column(db.Boolean)
    cron = db.Column(db.String(64))
    create_time = db.Column(db.DateTime, default=datetime.now)
