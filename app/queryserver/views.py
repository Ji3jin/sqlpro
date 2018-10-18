#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : views.py
# Author: jixin
# Date  : 18-10-17

from app import db
from ..models import CataLogInfo
from . import query
from ..core import baseapi
from flask import request
from .forms import CataLogForm


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
