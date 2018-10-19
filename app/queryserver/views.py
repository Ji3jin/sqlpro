#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : views.py
# Author: jixin
# Date  : 18-10-17

from app import db
from .models import CataLogInfo, DashBoard, ChartInfo
from . import query
from ..core import baseapi
from flask import request
from .forms import CataLogForm, DashBoardForm, ChartForm


@query.route('/query/catalog', methods=['POST'])
def add_catalog():
    cata_log = request.get_json()
    form = CataLogForm(data=cata_log)
    if form.validate():
        cata_log_info = CataLogInfo(catalog_name=form.catalog_name.data, hosts=form.hosts.data,
                                    username=form.username.data, password=form.password.data,
                                    catalog_type=form.catalog_type.data)
        db.session.add(cata_log_info)
        db.session.commit()
        return baseapi.success(cata_log_info.catalog_name)
    return baseapi.failed(form.errors, 500)


@query.route('/query/catalog', methods=['GET'])
def get_catalog_list():
    cata_log_infos = CataLogInfo.query.all()
    return baseapi.success([item.serialize() for item in cata_log_infos])


@query.route('/query/dashboard', methods=['POST'])
def add_dashboard():
    data = request.get_json()
    databoard_form = DashBoardForm(data=data.get('dashboard'))
    if databoard_form.validate():
        dashboard_info = DashBoard(name=databoard_form.name.data, description=databoard_form.desc.data)
        db.session.add(dashboard_info)
        db.session.commit()

        charts = data.get('charts')
        for item in charts:
            chart_form = ChartForm(data=item)
            chart_info = ChartInfo(dashboard_id=dashboard_info.id, chart_name=chart_form.name.data,
                                   description=chart_form.desc.data, catalog_name=chart_form.catalog_name.data,
                                   database_name=chart_form.database_name.data, table_name=chart_form.table_name.data,
                                   select_sql=chart_form.select_sql.data, xaxis=chart_form.xaxis.data,
                                   yaxis=chart_form.yaxis.data, template_type=chart_form.template_type.data,
                                   height=chart_form.height.data, width=chart_form.width.data, top=chart_form.top.data,
                                   left=chart_form.left.data)
            db.session.add(chart_info)
            db.session.commit()
        return baseapi.success("")
    return baseapi.failed(databoard_form.errors, 500)


@query.route('/query/dashboard', methods=['GET'])
def get_dashboard_list():
    dashboards = DashBoard.query.all()
    return baseapi.success([item.serialize() for item in dashboards])


@query.route('/query/dashboard/<int:id>', methods=['GET'])
def get_dashboard(id):
    dashboard = DashBoard.query.get(id)
    charts = ChartInfo.query.filter_by(dashboard_id=id).all()
    return baseapi.success({'databoard': dashboard.serialize(), 'charts': [item.serialize() for item in charts]})


@query.route('/query/chart/<int:id>', methods=['GET'])
def get_chart(id):
    chart = ChartInfo.query.get(id)
    # search data
    return baseapi.success(chart.serialize())