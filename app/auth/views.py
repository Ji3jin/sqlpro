#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : views.py
# Author: jixin
# Date  : 18-10-17
from flask import request, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required

from app import db
from .models import User
from . import auth
from .forms import LoginForm, RegisterForm
from ..core import baseapi


@auth.route('/auth/login', methods=['GET', 'POST'])
def login():
    user_data = request.form
    form = LoginForm(data=user_data)
    if request.method == 'POST' and form.validate():
        user = form.get_user()
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('query.index'))
    return render_template('login.html', form=form, error=form.errors)


@auth.route('/auth/register', methods=['GET', 'POST'])
def register():
    user_data = request.form
    form = RegisterForm(data=user_data)
    if request.method == 'POST' and form.validate():
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form, error=form.errors)


@auth.route('/auth/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
