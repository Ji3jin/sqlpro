#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : models.py
# Author: jixin
# Date  : 18-10-19
from datetime import datetime
from .. import db
from ..core.basemodel import Serializable
from enum import Enum


class ChartInfo(db.Model, Serializable):
    __tablename__ = 't_chart_info'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256),
                           nullable=False)
    chart_type = db.Column(db.String(64), nullable=False)
    x_axis_name = db.Column(db.String(64), nullable=False)
    y_axis_name = db.Column(db.String(64), nullable=False)
    select_sql = db.Column(db.String(1000), nullable=False)
    xaxis = db.Column(db.String(64))
    yaxis = db.Column(db.String(64))
    is_data_zoom = db.Column(db.Boolean)
    is_visual_map = db.Column(db.Boolean)
    is_wrangling = db.Column(db.Boolean)
    is_convert = db.Column(db.Boolean)
    is_public = db.Column(db.Boolean)
    operation = db.Column(db.Text)
    creator = db.Column(db.String(64), nullable=False)
    tag = db.Column(db.String(64))
    create_time = db.Column(db.DateTime, default=datetime.now)


class DashBoard(db.Model, Serializable):
    __tablename__ = 't_dashboard'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64),
                     nullable=False, unique=True, index=True)
    description = db.Column(db.String(256))
    is_public = db.Column(db.Boolean)
    creator = db.Column(db.String(64), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)


class DashBoardWithChart(db.Model, Serializable):
    __tablename__ = 't_relation'
    id = db.Column(db.Integer, primary_key=True)
    dashboard_id = db.Column(db.Integer)
    chart_id = db.Column(db.Integer)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    sort = db.Column(db.Integer)
    creator = db.Column(db.String(64), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)


class Catalog(db.Model, Serializable):
    __tablename__ = 't_catalog'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64),
                     nullable=False, unique=True, index=True)
    connector = db.Column(db.String(64), nullable=False)
    creator = db.Column(db.String(64), nullable=False)
    properties = db.Column(db.Text, nullable=False)
    public = db.Column(db.Boolean, default=False)
    create_time = db.Column(db.DateTime, default=datetime.now)


class SavedSql(db.Model, Serializable):
    __tablename__ = 't_saved_sql'
    id = db.Column(db.Integer, primary_key=True)
    sql = db.Column(db.String(1000), nullable=False)
    creator = db.Column(db.String(64), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)