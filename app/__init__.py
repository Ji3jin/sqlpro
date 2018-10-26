#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : __init__.py.py
# Author: jixin
# Date  : 18-10-17
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
from celery import Celery

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

config_name = os.getenv('FLASK_CONFIG') or 'default'
app = Flask(__name__)
app.config.from_object(config[config_name])

config[config_name].init_app(app)
db.init_app(app)
login_manager.init_app(app)


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'],
                    backend=app.config['CELERY_RESULT_BACKEND'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(app)

from .auth import auth as auth_blueprint

app.register_blueprint(auth_blueprint)
from .dataimport import etl as etl_blueprint

app.register_blueprint(etl_blueprint)
from .queryserver import query as query_blueprint

app.register_blueprint(query_blueprint)

with app.app_context():
    db.create_all()
