#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : views.py
# Author: jixin
# Date  : 18-10-17
from flask import request, jsonify
from flask_login import login_user, logout_user, login_required

from app import db
from ..models import User
from . import auth
from .forms import LoginForm, RegisterForm
from ..core import baseapi


@auth.route('/auth/login', methods=['POST'])
def login():
    user_data = request.get_json()
    form = LoginForm(data=user_data)
    if form.validate():
        user = form.get_user()
        login_user(user, remember=form.remember_me.data)
        return baseapi.success(user.username)
    return baseapi.failed(form.errors, 403)


@auth.route('/auth/register', methods=['POST'])
def register():
    user_data = request.get_json()
    form = RegisterForm(data=user_data)
    if form.validate():
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        return baseapi.success(user.username)
    return baseapi.failed(form.errors, 403)


@auth.route('/auth/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return baseapi.success("logout success")
