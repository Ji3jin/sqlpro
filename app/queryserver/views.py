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
from .chartview import ChartView
from ..wrangling.wloperation import WlOperation, get_recommend_operation
from ..wrangling.wranglingdf import WrangLingDF


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


@query.route('/query/sql', methods=['POST'])
def query_result():
    data = request.get_json()
    sql = data.get('sql', '')
    page_index = int(data.get('index', '1'))
    key = get_md5(sql)
    if query_cache.__contains__(key):
        paged_result = query_cache[key]
    else:
        paged_result = query_engine.query(sql, 100)
    data = paged_result.get_page(page_index)
    page_count = data.shape[0]
    return baseapi.success(data.to_dict(orient='split'), count=page_count, index=page_index)


@query.route('/query/operation', methods=['POST'])
def get_operation():
    data = request.get_json()
    sql = data.get('sql', '')
    page_index = int(data.get('index', '1'))
    x_index = int(data.get('x_index', '1'))
    y_index = int(data.get('y_index', '1'))
    key = get_md5(sql)
    if query_cache.__contains__(key):
        paged_result = query_cache[key]
    else:
        paged_result = query_engine.query(sql, 100)
    data = paged_result.get_page(page_index)
    wl_op = get_recommend_operation(data, x_index, y_index)
    return baseapi.success(wl_op)


@query.route('/query/extract', methods=['POST'])
def query_operation():
    data = request.get_json()
    sql = data.get('sql', '')
    page_index = int(data.get('index', '1'))
    wl_op = data.get('wl_op', None)
    key = get_md5(sql)
    if query_cache.__contains__(key):
        paged_result = query_cache[key]
    else:
        paged_result = query_engine.query(sql, 100)
    data = paged_result.get_page(page_index)
    wldf_key = get_md5("{0}_wldf".format(sql))
    if query_cache.__contains__(wldf_key):
        wl_df = query_cache[wldf_key]
        wl_df.dataframe = data
        data = wl_df.redo_dataframe(data)
    else:
        wl_df = WrangLingDF()
    if wl_op:
        wl_operation = WlOperation(attr_name=wl_op.get('attr_name'), is_callable=wl_op.get('is_callable'),
                                   param_num=wl_op.get('param_num'),
                                   op_type=wl_op.get('op_type'), op_param=wl_op.get('op_param'))
        data = wl_df.extract_dataframe(data, wl_operation)
    query_cache[wldf_key] = wl_df
    dbtypes = wl_df.dtypes
    return baseapi.success(data.to_dict(orient='split'), dbtypes=dbtypes)


@query.route('/query/extract', methods=['DELETE'])
def undo_operation():
    data = request.get_json()
    sql = data.get('sql', '')
    page_index = int(data.get('index', '1'))
    wldf_key = get_md5("{0}_wldf".format(sql))
    if query_cache.__contains__(wldf_key):
        key = get_md5(sql)
        if query_cache.__contains__(key):
            paged_result = query_cache[key]
        else:
            paged_result = query_engine.query(sql, 100)
        data = paged_result.get_page(page_index)
        wl_df = query_cache[wldf_key]
        data = wl_df.undo_dataframe(data)
        query_cache[wldf_key] = wl_df
        dbtypes = wl_df.dtypes
        return baseapi.success(data.to_dict(orient='split'), dbtypes=dbtypes)
    return baseapi.failed("no cache for wangling dataframe", 500)


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
    chart_data = ChartView.fill_data(chart, df)
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
        chart_info = ChartInfo(dashboard_id=chart_form.dashboard_id.data, chart_name=chart_form.name.data,
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
