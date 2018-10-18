#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : forms.py
# Author: jixin
# Date  : 18-10-17
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired
from ..core.catalog import CataLog


class CataLogForm(FlaskForm):
    catalog_name = StringField('CataLog', validators=[DataRequired()])
    hosts = StringField('Host and port', validators=[DataRequired()])
    username = StringField('UserName', validators=[DataRequired()])
    password = PasswordField('Password')
    catalog_type = SelectField('Type', choices=CataLog.choices(), coerce=CataLog.coerce)
