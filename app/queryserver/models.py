#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : models.py
# Author: jixin
# Date  : 18-10-19
from datetime import datetime
from .. import db
from ..core.basemodel import Serializable
from enum import Enum


class TemplateType(Enum):
    BAR = 'bar'
    LINE = 'line'
    PIE = 'pie'

    @classmethod
    def choices(cls):
        return [(choice, choice.name) for choice in cls]

    @classmethod
    def coerce(cls, item):
        return cls(item) if not isinstance(item, cls) else item

    def __str__(self):
        return str(self.value)


class ChartInfo(db.Model, Serializable):
    __tablename__ = 't_chart_info'
    id = db.Column(db.Integer, primary_key=True)
    dashboard_id = db.Column(db.Integer)
    chart_name = db.Column(db.String(64),
                           nullable=False, unique=True, index=True)
    description = db.Column(db.String(256))
    catalog_name = db.Column(db.String(64), nullable=False)
    database_name = db.Column(db.String(64), nullable=False)
    table_name = db.Column(db.String(64), nullable=False)
    select_sql = db.Column(db.String(1000), nullable=False)
    xaxis = db.Column(db.String(64))
    yaxis = db.Column(db.String(64))
    template_type = db.Column(db.Enum(TemplateType))
    height = db.Column(db.Integer)
    width = db.Column(db.Integer)
    top = db.Column(db.Integer)
    left = db.Column(db.Integer)
    create_time = db.Column(db.DateTime, default=datetime.now)


class DashBoard(db.Model, Serializable):
    __tablename__ = 't_dashboard'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64),
                     nullable=False, unique=True, index=True)
    description = db.Column(db.String(256))
    create_time = db.Column(db.DateTime, default=datetime.now)
