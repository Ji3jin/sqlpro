#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : views.py
# Author: jixin
# Date  : 18-10-17

from app import db
from .models import DashBoard, ChartInfo
from . import query
from ..core import baseapi
from flask import request
from .forms import DashBoardForm, ChartForm
from .pengine import query_engine, query_cache, get_md5
import pandas as pd
import json
from .chartview import chart_view


@query.route('/query/catalog', methods=['GET'])
def get_catalog_list():
    catalogs = query_engine.show_catalogs()
    return baseapi.success(catalogs.to_dict(orient='records'))


@query.route('/query/schemas/<string:catalog>', methods=['GET'])
def get_schema_list(catalog):
    schemas = query_engine.show_schemas(catalog)
    return baseapi.success(schemas.to_dict(orient='records'))


@query.route('/query/tables/<string:catalog>/<string:schema>', methods=['GET'])
def get_table_list(catalog, schema):
    tables = query_engine.show_tables(catalog, schema)
    return baseapi.success(tables.to_dict(orient='records'))


@query.route('/query/sql', methods=['GET'])
def query_result():
    sql = request.form.get('sql', "")
    page_index = int(request.form.get('index', '1'))
    key = get_md5(sql)
    if query_cache.__contains__(key):
        paged_result = query_cache[key]
    else:
        paged_result = query_engine.query(sql, 100)
    data = paged_result.get_page(page_index)
    page_count = data.shape[0]
    return baseapi.success(data.to_dict(orient='split'), count=page_count, index=page_index)


@query.route('/query/dashboard', methods=['POST'])
def add_dashboard():
    data = request.get_json()
    databoard_form = DashBoardForm(data=data)
    if databoard_form.validate():
        dashboard_info = DashBoard(name=databoard_form.name.data, description=databoard_form.desc.data)
        db.session.add(dashboard_info)
        db.session.commit()
        return baseapi.success("true")
    return baseapi.failed(databoard_form.errors, 500)


@query.route('/query/dashboard/<int:id>', methods=['DELETE'])
def delete_dashboard(id):
    dashboard = DashBoard.query.get(id)
    db.session.delete(dashboard)
    db.session.commit()
    return baseapi.success("true")


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
    df = query_engine.query_all(chart.select_sql)
    chart_data = chart_view.fill_data(chart, df)
    return baseapi.success(chart_data)


@query.route('/query/chart/<int:id>', methods=['DELETE'])
def delete_chart(id):
    chart = ChartInfo.query.get(id)
    db.session.delete(chart)
    db.session.commit()
    return baseapi.success("true")


@query.route('/query/chart', methods=['POST'])
def add_chart():
    chart_info = request.get_json()
    chart_form = ChartForm(data=chart_info)
    if chart_form.validate():
        chart_info = ChartInfo(dashboard_id=chart_form.id, chart_name=chart_form.name.data,
                               description=chart_form.desc.data, catalog_name=chart_form.catalog_name.data,
                               database_name=chart_form.database_name.data, table_name=chart_form.table_name.data,
                               select_sql=chart_form.select_sql.data, xaxis=chart_form.xaxis.data,
                               yaxis=chart_form.yaxis.data, template_type=chart_form.template_type.data,
                               height=chart_form.height.data, width=chart_form.width.data, top=chart_form.top.data,
                               left=chart_form.left.data)
        db.session.add(chart_info)
        db.session.commit()
        return baseapi.success("true")
    return baseapi.failed(chart_form.errors, 500)
