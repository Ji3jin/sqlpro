#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : __init__.py.py
# Author: jixin
# Date  : 18-10-17
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    from .dataimport import etl as etl_blueprint
    app.register_blueprint(etl_blueprint)
    from .queryserver import query as query_blueprint
    app.register_blueprint(query_blueprint)
    from .wrangling import wrangling as wrangling_blueprint
    app.register_blueprint(wrangling_blueprint)

    with app.app_context():
        db.create_all()

    return app
