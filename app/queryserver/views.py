#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : views.py
# Author: jixin
# Date  : 18-10-17

from app import db, app_config
from .models import DashBoard, ChartInfo, Catalog, SavedSql, DashBoardWithChart
from . import query
from ..core import baseapi
from flask import request, render_template, redirect, url_for, jsonify

from .pengine import query_engine, query_cache, get_md5
from .chartview import ChartView
from ..wrangling.wloperation import WlOperation, get_recommend_operation
from ..wrangling.wranglingdf import WrangLingDF
from flask_login import login_required, current_user
import json, requests
from operator import itemgetter
from itertools import groupby
from pyecharts_javascripthon.api import TRANSLATOR
from collections import defaultdict


@query.route('/', methods=['GET'])
@login_required
def index():
    saved_sqls = SavedSql.query.filter(SavedSql.creator == current_user.username).all()
    catalogs = Catalog.query.filter((Catalog.public == True) | (Catalog.creator == current_user.username)).all()
    catalog_tree = [
        {"id": item.id, "text": item.name, "param": item.name, "tags": [item.connector, ], "type": "catalog",
         "selectable": True, "lazyLoad": True}
        for
        item in catalogs]
    return render_template('index.html', catalogs=catalog_tree, saved_sqls=saved_sqls)


@query.route('/query/treeview', methods=['GET'])
@login_required
def get_treeview_nodes():
    node_type = request.args.get('type')
    param = request.args.get('param')
    params = param.split(',')
    if node_type == 'catalog':
        schemas = query_engine.show_schemas(*params)
        tree_node = [{"text": item["Schema"], "param": '{0},{1}'.format(param, item["Schema"]), "type": "schema",
                      "selectable": False, "lazyLoad": True} for index, item in schemas.iterrows()]
    elif node_type == 'schema':
        tables = query_engine.show_tables(*params)
        tree_node = [
            {"text": item["Table"], "param": '{0},{1}'.format(param, item["Table"]), "type": "table",
             "selectable": False,
             "lazyLoad": True} for index, item in tables.iterrows()]
    elif node_type == 'table':
        columns = query_engine.show_columns(*params)
        tree_node = [
            {"text": item['Column'], "type": "column", "tags": [item['Type'].split('(')[0], ], "selectable": False,
             "lazyLoad": False}
            for index, item in
            columns.iterrows()]
    else:
        tree_node = []
    return baseapi.success(data=tree_node)


@query.route('/query/catalog', methods=['POST'])
@login_required
def add_catalog():
    catalog_name = request.form.get('catalogName')
    connector_name = request.form.get('connectorName')
    is_public = request.form.get('isPublic')
    property_names = request.form.getlist('name[]')
    property_values = request.form.getlist('value[]')
    properties = {property_names[i]: property_values[i] for i in range(len(property_names))}
    post_data = {"catalogName": catalog_name, "connectorName": connector_name, "creator": current_user.username,
                 "properties": properties}
    headers = {'Content-Type': 'application/json'}
    r = requests.post("{0}/v1/catalog".format(app_config['PRESTO_HTTP_URI']), headers=headers,
                      data=json.dumps(post_data))
    if r.status_code != 200:
        return baseapi.exception("add catalog error")
    catalog = Catalog(name=catalog_name, connector=connector_name, public=True if is_public == 'on' else False,
                      creator=current_user.username, properties=json.dumps(properties))
    db.session.add(catalog)
    db.session.commit()
    return baseapi.success(
        data={"id": catalog.id, "text": catalog.name, "param": catalog.name, "type": "catalog", "selectable": True,
              "lazyLoad": True})


@query.route('/query/catalog', methods=['DELETE'])
@login_required
def delete_catalog():
    selected = request.form['ids']
    for id in selected.split(','):
        catalog = Catalog.query.get(int(id))
        del_data = {"catalogName": catalog.name, "connectorName": catalog.connector, "creator": catalog.creator,
                    "properties": json.loads(catalog.properties)}
        db.session.delete(catalog)
        db.session.commit()
        headers = {'Content-Type': 'application/json'}
        r = requests.delete("{0}/v1/catalog".format(app_config['PRESTO_HTTP_URI']), headers=headers,
                            data=json.dumps(del_data))
        if r.status_code != 200:
            return baseapi.exception("del catalog error")
    return baseapi.success("ok")


@query.route('/query/history', methods=['POST'])
@login_required
def save_query_sql():
    sql = request.form.get('sql')
    saved_sql = SavedSql(sql=sql, creator=current_user.username)
    db.session.add(saved_sql)
    db.session.commit()
    return baseapi.success("ok")


@query.route('/query/catalog', methods=['GET'])
@login_required
def get_catalog_list():
    catalogs = query_engine.show_catalogs()
    return baseapi.success(catalogs.to_dict(orient='records'))


@query.route('/query/schemas/<string:catalog>', methods=['GET'])
@login_required
def get_schema_list(catalog):
    schemas = query_engine.show_schemas(catalog)
    return baseapi.success(schemas.to_dict(orient='records'))


@query.route('/query/tables/<string:catalog>/<string:schema>', methods=['GET'])
@login_required
def get_table_list(catalog, schema):
    tables = query_engine.show_tables(catalog, schema)
    return baseapi.success(tables.to_dict(orient='records'))


@query.route('/query/sql', methods=['POST'])
@login_required
def query_result():
    sql = request.form.get('sql')
    page_index = int(request.form.get('index', '1'))
    page_index = 1 if page_index <= 0 else page_index
    key = get_md5(sql)
    if query_cache.__contains__(key):
        paged_result = query_cache[key]
    else:
        paged_result = query_engine.query(sql, 100)
    data = paged_result.get_page(page_index)
    page_count = data.shape[0]
    return baseapi.success(data=data.to_html(classes=["table", "table-bordered", "table-striped"]), count=page_count,
                           index=page_index, sql=sql)


@query.route('/query/chart', methods=['POST', 'GET'])
@login_required
def query_chart():
    if request.method == 'GET':
        sql = request.args.get('sql')
        is_wrangling = request.args.get('is_wrangling')
        page_index = int(request.form.get('index', '1'))
        page_index = 1 if page_index <= 0 else page_index
        key = get_md5(sql)
        if query_cache.__contains__(key):
            paged_result = query_cache[key]
        else:
            paged_result = query_engine.query(sql, 100)
        data = paged_result.get_page(page_index)
        xy_axis = data.columns.values.tolist()
        return render_template('chart.html', xy_axis=xy_axis, sql=sql, is_wrangling=is_wrangling)
    elif request.method == 'POST':
        id = request.args.get('id')
        sql = request.args.get('sql')
        is_wrangling = request.args.get('is_wrangling')
        title = request.form.get('chartTitle')
        chart_type = request.form.get('chartType')
        x_axis_name = request.form.get('xaxisName')
        y_axis_name = request.form.get('yaxisName')
        xaxis = request.form.get('xaxis')
        yaxis = request.form.getlist('yaxis')
        data_zoom = request.form.get('isDataZoom') == 'on'
        visual_map = request.form.get('isVisualMap') == 'on'
        is_convert = request.form.get('isConvert') == 'on'
        data = query_engine.query_all(sql)
        if is_wrangling == "true" and id > 0:
            chart_info = ChartInfo.query.get(id)
            wl_ops = json.loads(chart_info.operation)
            wl_df = WrangLingDF()
            wl_df.extract_record = wl_ops
            data = wl_df.redo_dataframe(data)
        chart_view = ChartView.create_instance("pyecharts", chart_type, title=title)
        for item in yaxis:
            chart_view.add(item, data[xaxis].tolist(), data[item].tolist(), xaxis_name=x_axis_name,
                           yaxis_name=y_axis_name, is_datazoom_show=data_zoom, is_visualmap=visual_map,
                           xaxis_name_pos='end', yaxis_name_pos='end', yaxis_name_gap=40, is_convert=is_convert,
                           maptype='china', geo_normal_color="#E5E7E9", geo_emphasis_color="#CACFD2")
    javascript_snippet = TRANSLATOR.translate(chart_view.options)
    return baseapi.success(data='true',
                           custom_function=javascript_snippet.function_snippet,
                           options=javascript_snippet.option_snippet, )


@query.route('/query/chart/save', methods=['POST'])
@login_required
def add_chart():
    sql = request.args.get('sql')
    is_wrangling = request.args.get('is_wrangling') == 'true'
    title = request.form.get('chartTitle')
    tag = request.form.get('tag')
    if not tag:
        tag = "Default"
    chart_type = request.form.get('chartType')
    x_axis_name = request.form.get('xaxisName')
    y_axis_name = request.form.get('yaxisName')
    xaxis = request.form.get('xaxis')
    yaxis = request.form.getlist('yaxis')
    data_zoom = request.form.get('isDataZoom') == 'on'
    visual_map = request.form.get('isVisualMap') == 'on'
    is_public = request.form.get('isPublic') == 'on'
    is_convert = request.form.get('isConvert') == 'on'
    operation = ""
    if is_wrangling:
        wldf_key = get_md5("{0}_wldf".format(sql))
        if query_cache.__contains__(wldf_key):
            wl_df = query_cache[wldf_key]
            operation = json.dumps(wl_df.extract_record)

    chart_info = ChartInfo(title=title, chart_type=chart_type,
                           x_axis_name=x_axis_name, y_axis_name=y_axis_name,
                           select_sql=sql, xaxis=xaxis,
                           yaxis=','.join(yaxis), is_data_zoom=data_zoom,
                           is_visual_map=visual_map, is_wrangling=is_wrangling, is_public=is_public,
                           operation=operation, tag=tag, is_convert=is_convert,
                           creator=current_user.username)
    db.session.add(chart_info)
    db.session.commit()
    return baseapi.success("true")


@query.route('/query/wrangling', methods=['POST', 'GET'])
@login_required
def data_wrangling():
    sql = request.args.get('sql')
    page_index = int(request.form.get('index', '1'))
    page_index = 1 if page_index <= 0 else page_index
    key = get_md5(sql)
    if query_cache.__contains__(key):
        paged_result = query_cache[key]
    else:
        paged_result = query_engine.query(sql, 100)
    data = paged_result.get_page(page_index)
    page_count = data.shape[0]
    wl_df = WrangLingDF()
    wl_df.pre_deal_data(data)
    wldf_key = get_md5("{0}_wldf".format(sql))
    query_cache[wldf_key] = wl_df
    dbtypes = wl_df.dtypes
    html = data.to_html(classes=["table", "table-condensed", "table-bordered"]).replace('<td>',
                                                                                        '<td><input type="text" class="form-control" value="').replace(
        '</td>', '"></td>')
    return render_template('wrangling.html', data=html, dtypes=dbtypes, count=page_count, sql=sql, index=page_index)


@query.route('/query/operation', methods=['POST'])
@login_required
def get_operation():
    sql = request.form.get('sql', '')
    page_index = int(request.form.get('index', '1'))
    x_index = int(request.form.get('x_index', '1'))
    y_index = int(request.form.get('y_index', '1'))
    key = get_md5(sql)
    if query_cache.__contains__(key):
        paged_result = query_cache[key]
    else:
        paged_result = query_engine.query(sql, 100)
    data = paged_result.get_page(page_index)
    wl_op = get_recommend_operation(data, x_index, y_index)
    return baseapi.success(data=wl_op, index=page_index, sql=sql)


@query.route('/query/extract', methods=['POST'])
@login_required
def query_operation():
    sql = request.form.get('sql')
    page_index = int(request.form.get('index', '1'))
    page_index = 1 if page_index <= 0 else page_index
    wl_op = request.form.get('wl_op', None)
    key = get_md5(sql)
    if query_cache.__contains__(key):
        paged_result = query_cache[key]
    else:
        paged_result = query_engine.query(sql, 100)
    data = paged_result.get_page(page_index)
    wldf_key = get_md5("{0}_wldf".format(sql))
    if query_cache.__contains__(wldf_key):
        wl_df = query_cache[wldf_key]
        data = wl_df.redo_dataframe(data)
    else:
        wl_df = WrangLingDF()
    if wl_op:
        wl_operation = WlOperation(attr_name=wl_op.get('attr_name'), is_callable=wl_op.get('is_callable'),
                                   param_num=wl_op.get('param_num'),
                                   op_type=wl_op.get('op_type'), op_param=wl_op.get('op_param'))
        data = wl_df.extract_dataframe(data, wl_operation)
    else:
        wl_df.pre_deal_data(data)
    query_cache[wldf_key] = wl_df
    dbtypes = wl_df.dtypes
    html = data.to_html(classes=["table", "table-condensed", "table-bordered"]).replace('<td>',
                                                                                        '<td><input type="text" class="form-control" value="').replace(
        '</td>', '"></td>')
    page_count = data.shape[0]
    return baseapi.success(data=html, dtypes=dbtypes, count=page_count, sql=sql, index=page_index)


@query.route('/query/extract', methods=['DELETE'])
@login_required
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
    return baseapi.failed("no cache for wrangling dataframe", 500)


@query.route('/query/dashboard', methods=['POST'])
@login_required
def add_dashboard():
    name = request.form.get('dashboardName')
    desc = request.form.get('dashboardDesc')
    is_public = request.form.get('isPublic') == 'on'
    dashboard_info = DashBoard(name=name, description=desc, is_public=is_public,
                               creator=current_user.username)
    db.session.add(dashboard_info)
    db.session.commit()
    return baseapi.success(name)


@query.route('/query/dashboard/<int:id>', methods=['DELETE'])
@login_required
def delete_dashboard(id):
    dashboard = DashBoard.query.get(id)
    db.session.delete(dashboard)
    db.session.commit()
    return baseapi.success("true")


@query.route('/query/dashboard/list', methods=['GET'])
@login_required
def get_dashboard_list():
    dashboards = DashBoard.query.filter(
        (DashBoard.creator == current_user.username) | (DashBoard.is_public == True)).all()
    chart_infos = ChartInfo.query.filter(ChartInfo.creator == current_user.username).order_by(ChartInfo.tag)
    select_nodes = [{"tag": tag, "nodes": [
        {"id": item.id, "text": item.title, "chart_type": item.chart_type} for item
        in items]} for tag, items in groupby(chart_infos, key=lambda m: m.tag)]
    return render_template('dashboard.html', dashboards=[{"name": item.name, "id": item.id} for item in dashboards],
                           chart_infos=select_nodes)


@query.route('/share/dashboard/<int:id>', methods=['GET'])
def share_dashboard(id):
    dashboard = DashBoard.query.get(id)
    charts = DashBoardWithChart.query.filter_by(dashboard_id=id).order_by(DashBoardWithChart.sort)
    return render_template('share.html', name=dashboard.name, id=dashboard.id,
                           charts=[{"id": item.chart_id, "width": item.width, "height": item.height} for item in
                                   charts])


@query.route('/share/chart/<int:id>', methods=['GET'])
def share_chart(id):
    chart = ChartInfo.query.get(id)
    data = query_engine.query_all(chart.select_sql)
    chart_view = ChartView.create_instance("pyecharts", chart.chart_type, title=chart.title)
    for item in chart.yaxis.split(','):
        chart_view.add(item, data[chart.xaxis].tolist(), data[item].tolist(), xaxis_name=chart.x_axis_name,
                       yaxis_name=chart.y_axis_name, is_datazoom_show=chart.is_data_zoom,
                       is_visualmap=chart.is_visual_map,
                       xaxis_name_pos='end', yaxis_name_pos='end', yaxis_name_gap=40, is_convert=chart.is_convert)
    javascript_snippet = TRANSLATOR.translate(chart_view.options)
    return baseapi.success(data="true", xy_axis=data.columns.values.tolist(),
                           custom_function=javascript_snippet.function_snippet,
                           options=javascript_snippet.option_snippet, chart_info=chart.serialize())


@query.route('/query/dashboard/<int:id>', methods=['GET', 'POST'])
@login_required
def get_dashboard(id):
    if request.method == 'GET':
        dashboard = DashBoard.query.get(id)
        charts = DashBoardWithChart.query.filter_by(dashboard_id=id).order_by(DashBoardWithChart.sort)
        return baseapi.success({'databoard': dashboard.name,
                                'charts': [{"id": item.chart_id, "width": item.width, "height": item.height} for item in
                                           charts]})
    elif request.method == 'POST':
        charts = json.loads(request.form.get('charts'))
        for chart in charts:
            d_chart = DashBoardWithChart(dashboard_id=id, chart_id=int(chart['chart_id']), width=float(chart['width']),
                                         height=float(chart['height']), sort=int(chart['sort']),
                                         creator=current_user.username)
            db.session.add(d_chart)
        db.session.commit()
        return baseapi.success("true")


@query.route('/query/chart/list', methods=['GET'])
@login_required
def get_chart_list():
    chart_infos = ChartInfo.query.filter(ChartInfo.creator == current_user.username).order_by(ChartInfo.tag)
    tree_nodes = [{"text": tag, "nodes": [
        {"id": item.id, "text": item.title, "tags": [item.chart_type, ], "selectable": True, "lazyLoad": False} for item
        in items],
                   "selectable": False} for tag, items in groupby(chart_infos, key=lambda m: m.tag)]
    return render_template('chartlist.html', tree_nodes=tree_nodes)


@query.route('/query/chart/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_chart(id):
    if request.method == 'GET':
        chart = ChartInfo.query.get(id)
        data = query_engine.query_all(chart.select_sql)
        chart_view = ChartView.create_instance("pyecharts", chart.chart_type, title=chart.title)
        for item in chart.yaxis.split(','):
            chart_view.add(item, data[chart.xaxis].tolist(), data[item].tolist(), xaxis_name=chart.x_axis_name,
                           yaxis_name=chart.y_axis_name, is_datazoom_show=chart.is_data_zoom,
                           is_visualmap=chart.is_visual_map,
                           xaxis_name_pos='end', yaxis_name_pos='end', yaxis_name_gap=40, is_convert=chart.is_convert,
                           maptype='china', geo_normal_color="#E5E7E9", geo_emphasis_color="#CACFD2")
        javascript_snippet = TRANSLATOR.translate(chart_view.options)
        return baseapi.success(data="true", xy_axis=data.columns.values.tolist(),
                               custom_function=javascript_snippet.function_snippet,
                               options=javascript_snippet.option_snippet, chart_info=chart.serialize())
    elif request.method == 'POST':
        title = request.form.get('chartTitle')
        chart_type = request.form.get('chartType')
        x_axis_name = request.form.get('xaxisName')
        y_axis_name = request.form.get('yaxisName')
        xaxis = request.form.get('xaxis')
        yaxis = request.form.getlist('yaxis')
        data_zoom = request.form.get('isDataZoom') == 'on'
        visual_map = request.form.get('isVisualMap') == 'on'
        is_convert = request.form.get('isConvert') == 'on'
        is_public = request.form.get('isPublic') == 'on'
        chart = ChartInfo.query.get(id).update(title=title, chart_type=chart_type,
                                               x_axis_name=x_axis_name, y_axis_name=y_axis_name, xaxis=xaxis,
                                               yaxis=yaxis, data_zoom=data_zoom, visual_map=visual_map,
                                               is_convert=is_convert, is_public=is_public)
        db.session.commit()
        return baseapi.success("true")


@query.route('/query/chart', methods=['DELETE'])
@login_required
def delete_chart():
    selected = request.form['ids']
    for id in selected.split(','):
        chart = ChartInfo.query.get(int(id))
        db.session.delete(chart)
        db.session.commit()
    return baseapi.success("true")
