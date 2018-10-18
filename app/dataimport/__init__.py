#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : __init__.py.py
# Author: jixin
# Date  : 18-10-17
from flask import Blueprint

etl = Blueprint('etl',__name__)

from . import views