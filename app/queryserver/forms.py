#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : forms.py
# Author: jixin
# Date  : 18-10-17
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField, FieldList, SelectField, FloatField, IntegerField, FormField, BooleanField
from wtforms.validators import DataRequired


class PropertyForm(FlaskForm):
    name = StringField('Name')
    value = StringField('Value')


class CatalogForm(FlaskForm):
    catalog_name = StringField('Name', validators=[DataRequired()])
    connector_name = StringField('Connector', validators=[DataRequired()])
    is_public = BooleanField('Public')
    properties = FieldList(FormField(PropertyForm), label='Property', min_entries=1)
    submit = SubmitField(label=u'Submit')


class DashBoardForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    desc = StringField('Desc')
