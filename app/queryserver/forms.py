#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : forms.py
# Author: jixin
# Date  : 18-10-17
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired
from .models import TemplateType


class DashBoardForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    desc = StringField('Desc')


class ChartForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    desc = StringField('Desc')
    catalog_name = StringField('Catalog', validators=[DataRequired()])
    database_name = StringField('Database', validators=[DataRequired()])
    table_name = StringField('Table', validators=[DataRequired()])
    select_sql = StringField('SQL', validators=[DataRequired()])
    xaxis = StringField('X axis', validators=[DataRequired()])
    yaxis = StringField('Y axis', validators=[DataRequired()])
    template_type = SelectField('Type', choices=TemplateType.choices(), coerce=TemplateType.coerce)
    dashboard_id = IntegerField('DashBoard', validators=[DataRequired()])
    height = FloatField('Height')
    width = FloatField('Width')
    top = FloatField('Top')
    left = FloatField('Left')
