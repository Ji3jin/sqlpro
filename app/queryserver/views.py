#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : views.py
# Author: jixin
# Date  : 18-10-17

from app import db
from .models import DashBoard, ChartInfo, Catalog, SavedSql,DashBoardWithChart
from . import query
from ..core import baseapi
from flask import request, render_template, redirect, url_for, jsonify
from .forms import DashBoardForm, CatalogForm

from .pengine import query_engine, query_cache, get_md5
from .chartview import ChartView
from ..wrangling.wloperation import WlOperation, get_recommend_operation
from ..wrangling.wranglingdf import WrangLingDF
from flask_login import login_required, current_user
import json
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
        db.session.delete(catalog)
        db.session.commit()

        # delete from presto
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
        sql = request.args.get('sql')
        is_wrangling = request.args.get('is_wrangling')
        title = request.form.get('chartTitle')
        sub_title = request.form.get('chartSubTitle')
        chart_type = request.form.get('chartType')
        x_axis_name = request.form.get('xaxisName')
        y_axis_name = request.form.get('yaxisName')
        xaxis = request.form.get('xaxis')
        yaxis = request.form.getlist('yaxis')
        data_zoom = request.form.get('isDataZoom') == 'on'
        visual_map = request.form.get('isVisualMap') == 'on'
        is_convert = request.form.get('isConvert') == 'on'
        data = query_engine.query_all(sql)
        chart_view = ChartView.create_instance("pyecharts", chart_type, title=title, subtitle=sub_title)
        for item in yaxis:
            chart_view.add(item, data[xaxis].tolist(), data[item].tolist(), xaxis_name=x_axis_name,
                           yaxis_name=y_axis_name, is_datazoom_show=data_zoom, is_visualmap=visual_map,
                           xaxis_name_pos='end', yaxis_name_pos='end', yaxis_name_gap=40, is_convert=is_convert)
        javascript_snippet = TRANSLATOR.translate(chart_view.options)
        return baseapi.success(data='true',
                               custom_function=javascript_snippet.function_snippet,
                               options=javascript_snippet.option_snippet, )


@query.route('/query/chart/save', methods=['POST'])
def add_chart():
    sql = request.args.get('sql')
    is_wrangling = request.args.get('is_wrangling') == 'true'
    title = request.form.get('chartTitle')
    sub_title = request.form.get('chartSubTitle')
    chart_type = request.form.get('chartType')
    x_axis_name = request.form.get('xaxisName')
    y_axis_name = request.form.get('yaxisName')
    xaxis = request.form.get('xaxis')
    yaxis = request.form.getlist('yaxis')
    data_zoom = request.form.get('isDataZoom') == 'on'
    visual_map = request.form.get('isVisualMap') == 'on'
    is_public = request.form.get('isPublic') == 'on'
    operation = ""
    if is_wrangling:
        wldf_key = get_md5("{0}_wldf".format(sql))
        if query_cache.__contains__(wldf_key):
            wl_df = query_cache[wldf_key]
            operation = json.dumps(wl_df.extract_record)

    chart_info = ChartInfo(title=title,
                           sub_title=sub_title, chart_type=chart_type,
                           x_axis_name=x_axis_name, y_axis_name=y_axis_name,
                           select_sql=sql, xaxis=xaxis,
                           yaxis=','.join(yaxis), is_data_zoom=data_zoom,
                           is_visual_map=visual_map, is_wrangling=is_wrangling, is_public=is_public
                           operation=operation,
                           creator=current_user.username)
    db.session.add(chart_info)
    db.session.commit()
    return baseapi.success("true")


@query.route('/query/wrangling', methods=['POST', 'GET'])
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
def add_dashboard():
    data = request.get_json()
    databoard_form = DashBoardForm(data=data)
    if databoard_form.validate():
        dashboard_info = DashBoard(name=databoard_form.name.data, description=databoard_form.desc.data,
                                   creator=current_user.username)
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
    dashboards = DashBoard.query.filter((DashBoard.creator == current_user.username)|(DashBoard.is_public==True).all()
    result = []
    for item in dashboards:
        chart_count = DashBoardWithChart.query.filter(DashBoardWithChart.dashboard_id==item.id).count()
        result.append({"name":item.name,"chart_count":chart_count})
    return render_template('dashboard.html', dashboards=result)


@query.route('/query/dashboard/<int:id>', methods=['GET'])
def get_dashboard(id):
    dashboard = DashBoard.query.get(id)
    charts = ChartInfo.query.filter_by(dashboard_id=id).all()
    return baseapi.success({'databoard': dashboard.serialize(), 'charts': [item.serialize() for item in charts]})


@query.route('/query/chart', methods=['GET'])
def get_chart_list():
    chart_infos = ChartInfo.query.filter(ChartInfo.creator == current_user.username).all()
    chart_infos.sort(key=itemgetter('tag'))
    tree_nodes = [{"text": tag, "nodes": [{"id":item.id,"text": item.title, "tags": [item.chart_type, ], "selectable": True, "lazyLoad": False}],
      "selectable": False} for tag, item in groupby(chart_infos, key=itemgetter('tag'))]
    return render_template('chartlist.html', tree_nodes=tree_nodes)


@query.route('/query/chart/<int:id>', methods=['GET','POST'])
def edit_chart(id):
    chart = ChartInfo.query.get(id)
    if request.method == 'GET':
        data = query_engine.query_all(sql)
        chart_view = ChartView.create_instance("pyecharts", chart.chart_type, title=chart.title, subtitle=chart.sub_title)
        for item in chart.yaxis.split(','):
            chart_view.add(item, data[chart.xaxis].tolist(), data[item].tolist(), xaxis_name=chart.x_axis_name,
                            yaxis_name=chart.y_axis_name, is_datazoom_show=chart.data_zoom, is_visualmap=chart.visual_map,
                            xaxis_name_pos='end', yaxis_name_pos='end', yaxis_name_gap=40, is_convert=chart.is_convert)
        javascript_snippet = TRANSLATOR.translate(chart_view.options)
        return baseapi.success(data='true',
                                custom_function=javascript_snippet.function_snippet,
                                options=javascript_snippet.option_snippet,chart_info=chart )
    elif request.method=='POST':
        title = request.form.get('chartTitle')
        sub_title = request.form.get('chartSubTitle')
        chart_type = request.form.get('chartType')
        x_axis_name = request.form.get('xaxisName')
        y_axis_name = request.form.get('yaxisName')
        xaxis = request.form.get('xaxis')
        yaxis = request.form.getlist('yaxis')
        data_zoom = request.form.get('isDataZoom') == 'on'
        visual_map = request.form.get('isVisualMap') == 'on'
        is_convert = request.form.get('isConvert') == 'on'
        is_public = request.form.get('isPublic') == 'on'
        chart.title=title
        chart.sub_title=sub_title
        chart.chart_type=chart_type
        chart.x_axis_name=x_axis_name
        chart.y_axis_name=y_axis_name
        chart.xaxis=xaxis
        chart.yaxis=yaxis
        chart.data_zoom=data_zoom
        chart.visual_map=visual_map
        chart.is_convert=is_convert
        chart.is_public=is_public
        db.session.commit()
        return baseapi.success("true")


@query.route('/query/chart/<int:id>', methods=['DELETE'])
def delete_chart(id):
    chart = ChartInfo.query.get(id)
    db.session.delete(chart)
    db.session.commit()
    return baseapi.success("true")
